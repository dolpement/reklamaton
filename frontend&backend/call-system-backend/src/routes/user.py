from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import db, User
import re

user_bp = Blueprint('user', __name__)

def validate_email(email):
    """Проверка валидности email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@user_bp.route('/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Валидация данных
    if not username or len(username) < 3:
        return jsonify({'error': 'Имя пользователя должно содержать минимум 3 символа'}), 400
    
    if not email or not validate_email(email):
        return jsonify({'error': 'Некорректный email адрес'}), 400
    
    if not password or len(password) < 6:
        return jsonify({'error': 'Пароль должен содержать минимум 6 символов'}), 400
    
    # Проверка на существование пользователя
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
    
    # Создание нового пользователя
    hashed_password = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=hashed_password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Автоматический вход после регистрации
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Пользователь успешно зарегистрирован',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при создании пользователя'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """Вход пользователя"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Данные не предоставлены'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Имя пользователя и пароль обязательны'}), 400
    
    # Поиск пользователя
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401
    
    # Создание сессии
    session['user_id'] = user.id
    session['username'] = user.username
    
    return jsonify({
        'message': 'Успешный вход',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

@user_bp.route("/logout", methods=["POST"])
def logout():
    """Выход пользователя"""
    session.clear()
    return jsonify({"message": "Выход выполнен успешно"})

@user_bp.route("/search", methods=["GET"])
def search_users():
    """Поиск пользователей по нику"""
    if "user_id" not in session:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"users": []})
    
    current_user_id = session["user_id"]
    
    # Поиск пользователей по нику (исключая текущего пользователя)
    users = User.query.filter(
        User.username.ilike(f"%{query}%"),
        User.id != current_user_id
    ).limit(10).all()
    
    return jsonify({
        "users": [user.to_dict() for user in users]
    })

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """Получение профиля текущего пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Пользователь не авторизован'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

@user_bp.route('/users', methods=['GET'])
def get_users():
    """Получение списка всех пользователей (только для авторизованных)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Пользователь не авторизован'}), 401
    
    users = User.query.all()
    current_user_id = session['user_id']
    
    # Исключаем текущего пользователя из списка
    users_list = []
    for user in users:
        if user.id != current_user_id:
            users_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'online': False  # Будет обновляться через Socket.IO
            })
    
    return jsonify(users_list), 200

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

