import requests
import json
from flask import Blueprint, request, jsonify, session
from functools import wraps

yandex_gpt_bp = Blueprint('yandex_gpt', __name__)

# Конфигурация Яндекс GPT
YANDEX_GPT_CONFIG = {
    'api_key': 'AQVNw4eXZXjCT-HuhQR7Bq-YEryqLxZ0O1WzoFs_',
    'folder_id': 'aje3gubmau629vgut184',
    'model_uri': 'gpt://aje3gubmau629vgut184/yandexgpt-lite/latest',
    'api_url': 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

def create_yandex_gpt_request(messages, temperature=0.6):
    """Создает запрос к Яндекс GPT API"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {YANDEX_GPT_CONFIG["api_key"]}'
    }
    
    data = {
        'modelUri': YANDEX_GPT_CONFIG['model_uri'],
        'completionOptions': {
            'stream': False,
            'temperature': temperature,
            'maxTokens': 2000
        },
        'messages': messages
    }
    
    return headers, data

@yandex_gpt_bp.route('/chat', methods=['POST'])
@login_required
def chat_with_agent():
    """Обработка чата с AI агентом через Яндекс GPT"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Нет данных в запросе'}), 400
            
        user_message = data.get('message', '')
        agent_character = data.get('character', '')
        chat_history = data.get('history', [])
        
        if not user_message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        # Формируем системное сообщение на основе характера агента
        system_message = f"""Ты AI агент с следующими характеристиками: {agent_character}
        
Отвечай в соответствии с этим характером. Будь дружелюбным собеседником. 
Отвечай на русском языке. Поддерживай естественный диалог."""
        
        # Формируем историю сообщений для API
        messages = [{'role': 'system', 'text': system_message}]
        
        # Добавляем историю чата
        for msg in chat_history[-10:]:  # Берем последние 10 сообщений
            messages.append({
                'role': msg.get('role', 'user'),
                'text': msg.get('text', '')
            })
        
        # Добавляем текущее сообщение пользователя
        messages.append({
            'role': 'user',
            'text': user_message
        })
        
        # Отправляем запрос к Яндекс GPT
        headers, request_data = create_yandex_gpt_request(messages)
        
        response = requests.post(
            YANDEX_GPT_CONFIG['api_url'],
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if 'result' in result and 'alternatives' in result['result']:
                alternatives = result['result']['alternatives']
                if alternatives and len(alternatives) > 0:
                    ai_response = alternatives[0]['message']['text']
                    
                    return jsonify({
                        'success': True,
                        'response': ai_response,
                        'timestamp': data.get('timestamp')
                    })
                else:
                    return jsonify({'error': 'Пустой ответ от AI'}), 500
            else:
                return jsonify({'error': 'Неверный формат ответа от API'}), 500
        else:
            error_text = response.text
            print(f"Ошибка Яндекс GPT API: {response.status_code} - {error_text}")
            return jsonify({'error': f'Ошибка API: {response.status_code}'}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Превышено время ожидания ответа от AI'}), 504
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к Яндекс GPT: {str(e)}")
        return jsonify({'error': 'Ошибка соединения с AI сервисом'}), 503
    except Exception as e:
        print(f"Неожиданная ошибка в chat_with_agent: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@yandex_gpt_bp.route('/test', methods=['GET'])
@login_required
def test_yandex_gpt():
    """Тестовый эндпоинт для проверки работы Яндекс GPT"""
    try:
        test_messages = [
            {
                'role': 'system',
                'text': 'Ты дружелюбный AI ассистент. Отвечай кратко и по делу.'
            },
            {
                'role': 'user',
                'text': 'Привет! Как дела?'
            }
        ]
        
        headers, request_data = create_yandex_gpt_request(test_messages)
        
        response = requests.post(
            YANDEX_GPT_CONFIG['api_url'],
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'test_response': result,
                'config': {
                    'model_uri': YANDEX_GPT_CONFIG['model_uri'],
                    'folder_id': YANDEX_GPT_CONFIG['folder_id']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'API Error: {response.status_code}',
                'response_text': response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

