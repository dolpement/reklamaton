#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from models.user import db, User

def init_database():
    """Инициализация базы данных"""
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Создаем директорию для базы данных
        db_dir = os.path.join(os.path.dirname(__file__), 'database')
        os.makedirs(db_dir, exist_ok=True)
        
        # Удаляем старую базу данных если существует
        db_path = os.path.join(db_dir, 'app.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Удалена старая база данных")
        
        # Создаем новые таблицы
        db.create_all()
        print("База данных успешно создана")
        
        # Проверяем структуру
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Созданные таблицы: {tables}")
        
        if 'user' in tables:
            columns = inspector.get_columns('user')
            print("Колонки в таблице user:")
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")

if __name__ == '__main__':
    init_database()

