from flask import Blueprint, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from src.models.user import db, User
from datetime import datetime
import uuid
import time

call_bp = Blueprint("call", __name__)

# Хранилище активных звонков и подключенных пользователей
active_calls = {}
connected_users = {}  # socket_id -> user_data
user_sockets = {}     # user_id -> socket_id
drone_status = {}

def init_socketio(socketio):
    """Инициализация Socket.IO событий для системы звонка"""
    
    @socketio.on("connect")
    def handle_connect():
        print(f"Socket connected: {request.sid}")
    
    @socketio.on("disconnect")
    def handle_disconnect():
        print(f"Socket disconnected: {request.sid}")
        
        # Найти пользователя по socket_id
        user_data = connected_users.get(request.sid)
        if user_data:
            user_id = user_data["id"]
            
            # Обновить статус пользователя в базе данных
            user = User.query.get(user_id)
            if user:
                user.is_online = False
                user.last_seen = datetime.utcnow()
                db.session.commit()
            
            # Удалить из хранилищ
            del connected_users[request.sid]
            if user_id in user_sockets:
                del user_sockets[user_id]
            
            # Уведомить других пользователей
            socketio.emit("user_disconnected", {"user_id": user_id}, broadcast=True, include_self=False)
        
        # Завершить все звонки пользователя
        for call_id, call_data in list(active_calls.items()):
            if request.sid in [call_data.get("caller_socket"), call_data.get("callee_socket")]:
                del active_calls[call_id]
                socketio.emit("call_ended", {"call_id": call_id}, room=call_id)
    
    @socketio.on("authenticate")
    def handle_authenticate():
        """Аутентификация пользователя через Socket.IO"""
        if "user_id" not in session:
            emit("auth_error", {"message": "Пользователь не авторизован"})
            return
        
        user_id = session["user_id"]
        username = session["username"]
        
        # Обновить статус пользователя в базе данных
        user = User.query.get(user_id)
        if user:
            user.is_online = True
            user.last_seen = datetime.utcnow()
            db.session.commit()
        
        # Сохранить связь socket_id -> user_data
        user_data = {
            "id": user_id,
            "username": username,
            "socket_id": request.sid
        }
        connected_users[request.sid] = user_data
        user_sockets[user_id] = request.sid
        
        emit("authenticated", {"user": user_data})
        
        # Отправить список онлайн пользователей
        online_users = []
        for socket_id, user_info in connected_users.items():
            if user_info["id"] != user_id:  # Исключить текущего пользователя
                online_users.append(user_info)
        
        emit("online_users", online_users)
        
        # Уведомить других пользователей о подключении
        emit("user_connected", user_data, broadcast=True, include_self=False)
    
    @socketio.on("initiate_call")
    def handle_initiate_call(data):
        """Инициация звонка"""
        if "user_id" not in session:
            emit("call_error", {"message": "Пользователь не авторизован"})
            return
        
        caller_id = session["user_id"]
        callee_id = data.get("callee_id")
        call_type = data.get("call_type", "audio")  # "audio" или "video"
        character = data.get("character", "default") # Добавлено для AI агентов
        
        # Проверить, что вызываемый пользователь существует
        callee = User.query.get(callee_id)
        if not callee:
            emit("call_error", {"message": "Пользователь не найден"})
            return
        
        # Проверить, что вызываемый пользователь онлайн
        callee_socket = user_sockets.get(callee_id)
        if not callee_socket:
            emit("call_error", {"message": "Пользователь не в сети"})
            return
        
        call_id = str(uuid.uuid4())
        active_calls[call_id] = {
            "id": call_id,
            "caller_id": caller_id,
            "callee_id": callee_id,
            "caller_socket": request.sid,
            "callee_socket": callee_socket,
            "type": call_type,
            "character": character, # Сохраняем character
            "status": "ringing",
            "created_at": time.time()
        }
        
        # Получить данные пользователей
        caller = User.query.get(caller_id)
        
        # Уведомить вызывающего о начале звонка
        emit("call_initiated", {
            "call_id": call_id,
            "callee": callee.to_dict(),
            "type": call_type
        })
        
        # Уведомить вызываемого о входящем звонке
        socketio.emit("incoming_call", {
            "call_id": call_id,
            "caller": caller.to_dict(),
            "type": call_type,
            "character": character # Передаем character
        }, room=callee_socket)
    
    @socketio.on("accept_call")
    def handle_accept_call(data):
        """Принятие звонка"""
        if "user_id" not in session:
            emit("call_error", {"message": "Пользователь не авторизован"})
            return
        
        call_id = data.get("call_id")
        
        if call_id not in active_calls:
            emit("call_error", {"message": "Звонок не найден"})
            return
        
        call_data = active_calls[call_id]
        if call_data["callee_id"] != session["user_id"]:
            emit("call_error", {"message": "Недостаточно прав"})
            return
        
        # Обновить статус звонка
        active_calls[call_id]["status"] = "active"
        
        # Присоединить обоих пользователей к комнате звонка
        join_room(call_id)
        socketio.emit("join_room", {"room": call_id}, room=call_data["caller_socket"])
        
        # Получить данные участников
        caller = User.query.get(call_data["caller_id"])
        callee = User.query.get(call_data["callee_id"])
        
        # Уведомить обоих о принятии звонка
        socketio.emit("call_accepted", {
            "call_id": call_id,
            "participants": [caller.to_dict(), callee.to_dict()],
            "type": call_data["type"], # Передаем тип звонка
            "character": call_data["character"] # Передаем character
        }, room=call_id)
        
        # Если это видеозвонок, активировать дрон
        if call_data["type"] == "video":
            drone_status[call_id] = "connecting"
            socketio.emit("drone_status_update", {
                "call_id": call_id,
                "status": "connecting"
            }, room=call_id)
            
            # Имитация подключения дрона
            socketio.sleep(2)
            drone_status[call_id] = "connected"
            socketio.emit("drone_status_update", {
                "call_id": call_id,
                "status": "connected"
            }, room=call_id)
    
    @socketio.on("decline_call")
    def handle_decline_call(data):
        """Отклонение звонка"""
        if "user_id" not in session:
            emit("call_error", {"message": "Пользователь не авторизован"})
            return
        
        call_id = data.get("call_id")
        
        if call_id not in active_calls:
            emit("call_error", {"message": "Звонок не найден"})
            return
        
        call_data = active_calls[call_id]
        
        # Уведомить вызывающего об отклонении
        socketio.emit("call_declined", {"call_id": call_id}, room=call_data["caller_socket"])
        
        # Удалить звонок
        del active_calls[call_id]
    
    @socketio.on("end_call")
    def handle_end_call(data):
        """Завершение звонка"""
        if "user_id" not in session:
            emit("call_error", {"message": "Пользователь не авторизован"})
            return
        
        call_id = data.get("call_id")
        
        if call_id not in active_calls:
            emit("call_error", {"message": "Звонок не найден"})
            return
        
        # Уведомить всех участников о завершении звонка
        socketio.emit("call_ended", {"call_id": call_id}, room=call_id)
        
        # Отключить дрон если был активен
        if call_id in drone_status:
            del drone_status[call_id]
        
        # Удалить звонок
        del active_calls[call_id]
    
    @socketio.on("webrtc_offer")
    def handle_webrtc_offer(data):
        """Обработка WebRTC offer"""
        call_id = data.get("call_id")
        offer = data.get("offer")
        
        if call_id in active_calls:
            call_data = active_calls[call_id]
            # Переслать offer другому участнику
            target_socket = call_data["callee_socket"] if call_data["caller_socket"] == request.sid else call_data["caller_socket"]
            socketio.emit("webrtc_offer", {
                "call_id": call_id,
                "offer": offer,
                "from": request.sid
            }, room=target_socket)
    
    @socketio.on("webrtc_answer")
    def handle_webrtc_answer(data):
        """Обработка WebRTC answer"""
        call_id = data.get("call_id")
        answer = data.get("answer")
        
        if call_id in active_calls:
            call_data = active_calls[call_id]
            # Переслать answer другому участнику
            target_socket = call_data["caller_socket"] if call_data["callee_socket"] == request.sid else call_data["callee_socket"]
            socketio.emit("webrtc_answer", {
                "call_id": call_id,
                "answer": answer,
                "from": request.sid
            }, room=target_socket)
    
    @socketio.on("webrtc_ice_candidate")
    def handle_ice_candidate(data):
        """Обработка ICE candidates"""
        call_id = data.get("call_id")
        candidate = data.get("candidate")
        
        if call_id in active_calls:
            call_data = active_calls[call_id]
            # Переслать ICE candidate другому участнику
            current_user_id = session.get("user_id")
            target_user_id = call_data["callee_id"] if current_user_id == call_data["caller_id"] else call_data["caller_id"]
            
            target_socket = None
            for socket_id, user_data in connected_users.items():
                if user_data["id"] == target_user_id:
                    target_socket = socket_id
                    break
                    
            if target_socket:
                emit("webrtc_ice_candidate", {
                    "call_id": call_id,
                    "candidate": candidate,
                    "from": request.sid
                }, room=target_socket)

# REST API маршруты
@call_bp.route("/online-users", methods=["GET"])
def get_online_users():
    """Получить список онлайн пользователей"""
    if "user_id" not in session:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    current_user_id = session["user_id"]
    online_users = []
    
    for socket_id, user_data in connected_users.items():
        if user_data["id"] != current_user_id:
            online_users.append(user_data)
    
    return jsonify(online_users)

@call_bp.route("/calls", methods=["GET"])
def get_active_calls():
    """Получить список активных звонков"""
    if "user_id" not in session:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    return jsonify(list(active_calls.values()))

@call_bp.route("/drone/takeoff", methods=["GET", "POST"])
def drone_takeoff():
    """API для взлета дрона"""
    if "user_id" not in session:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    return jsonify({"status": "success", "message": "Drone takeoff initiated"})

@call_bp.route("/drone/audio", methods=["GET", "POST"])
def drone_audio():
    """API для подключения дрона к аудиопотоку"""
    if "user_id" not in session:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    character = request.args.get("character")
    stream_url = request.args.get("streamUrl")
    
    return jsonify({
        "status": "success", 
        "message": "Drone connected to audio stream",
        "character": character,
        "stream_url": stream_url
    })

@call_bp.route("/drone/turn", methods=["GET", "POST"])
def drone_turn():
    """API для управления поведением дрона"""
    if "user_id" not in session:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    character = request.args.get("character")
    
    return jsonify({
        "status": "success",
        "message": "Drone behavior adjusted",
        "character": character
    })

@call_bp.route("/stream/audio/<contact_id>/<timestamp>")
def audio_stream(contact_id, timestamp):
    """Эндпоинт для аудиопотока"""
    if "user_id" not in session:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    # Здесь должна быть логика для отдачи аудиопотока
    # Пока возвращаем заглушку
    return jsonify({
        "status": "streaming",
        "contact_id": contact_id,
        "timestamp": timestamp,
        "message": "Audio stream endpoint (placeholder)"
    })





