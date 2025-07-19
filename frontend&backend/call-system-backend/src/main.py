import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, session
from flask_socketio import SocketIO
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.call import call_bp, init_socketio
from routes.yandex_assistant import yandex_assistant_bp
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# Включаем CORS для всех доменов с поддержкой credentials
CORS(app, origins="*", supports_credentials=True)

# Инициализация Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", manage_sessions=False)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(call_bp, url_prefix='/api')
app.register_blueprint(yandex_assistant_bp, url_prefix='/api/assistant')

# Инициализация Socket.IO событий для системы звонка
init_socketio(socketio)

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3001, debug=True, allow_unsafe_werkzeug=True)

