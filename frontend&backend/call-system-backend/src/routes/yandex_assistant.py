import requests
import json
from flask import Blueprint, request, jsonify, session
from functools import wraps

yandex_assistant_bp = Blueprint('yandex_assistant', __name__)

# Конфигурация Яндекс Assistant
YANDEX_ASSISTANT_CONFIG = {
    'api_key': 'AQVNwKAjyDQ_7V_wK8GPTd1rZqtBM6mAWRwdPZ1I',
    'folder_id': 'aje0k0hsgd1vtlfv0au1',
    'api_url': 'https://llm.api.cloud.yandex.net/assistants/v1'
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Требуется авторизация'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Хранилище ассистентов и тредов для каждого пользователя
user_assistants = {}
user_threads = {}

def create_assistant(character_description):
    """Создает ассистента с заданным характером"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {YANDEX_ASSISTANT_CONFIG["api_key"]}'
    }
    
    system_prompt = f"""
    {character_description}
    
    При общении:
    1. Отвечай в соответствии с описанным характером
    2. Будь дружелюбным и естественным собеседником
    3. Отвечай на русском языке
    4. Если не знаешь ответа, честно признайся в этом
    5. Поддерживай естественный диалог
    """
    
    data = {
        'folderId': YANDEX_ASSISTANT_CONFIG['folder_id'],
        'modelUri': f"gpt://{YANDEX_ASSISTANT_CONFIG['folder_id']}/yandexgpt/latest",
        'instruction': system_prompt,
        'ttlDays': 7,
        'expirationPolicy': 'since_last_active',
        'maxTokens': 1000
    }
    
    try:
        response = requests.post(
            f"{YANDEX_ASSISTANT_CONFIG['api_url']}/assistants",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка создания ассистента: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при создании ассистента: {str(e)}")
        return None

def create_thread():
    """Создает тред для общения"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {YANDEX_ASSISTANT_CONFIG["api_key"]}'
    }
    
    data = {
        'folderId': YANDEX_ASSISTANT_CONFIG['folder_id'],
        'name': 'ChatThread',
        'ttlDays': 5,
        'expirationPolicy': 'static'
    }
    
    try:
        response = requests.post(
            f"{YANDEX_ASSISTANT_CONFIG['api_url']}/threads",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка создания треда: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при создании треда: {str(e)}")
        return None

def send_message_to_thread(thread_id, message):
    """Отправляет сообщение в тред"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {YANDEX_ASSISTANT_CONFIG["api_key"]}'
    }
    
    data = {
        'text': message
    }
    
    try:
        response = requests.post(
            f"{YANDEX_ASSISTANT_CONFIG['api_url']}/threads/{thread_id}/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка отправки сообщения: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {str(e)}")
        return None

def run_assistant(assistant_id, thread_id):
    """Запускает ассистента для обработки треда"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {YANDEX_ASSISTANT_CONFIG["api_key"]}'
    }
    
    data = {
        'assistantId': assistant_id,
        'stream': False
    }
    
    try:
        response = requests.post(
            f"{YANDEX_ASSISTANT_CONFIG['api_url']}/threads/{thread_id}/runs",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка запуска ассистента: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при запуске ассистента: {str(e)}")
        return None

def get_run_result(thread_id, run_id):
    """Получает результат выполнения ассистента"""
    headers = {
        'Authorization': f'Api-Key {YANDEX_ASSISTANT_CONFIG["api_key"]}'
    }
    
    try:
        response = requests.get(
            f"{YANDEX_ASSISTANT_CONFIG['api_url']}/threads/{thread_id}/runs/{run_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка получения результата: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка при получении результата: {str(e)}")
        return None

@yandex_assistant_bp.route('/chat', methods=['POST'])
@login_required
def chat_with_assistant():
    """Обработка чата с AI агентом через Яндекс Assistant"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Нет данных в запросе'}), 400
            
        user_message = data.get('message', '')
        agent_character = data.get('character', '')
        agent_id = data.get('agent_id', 'default')
        user_id = session.get('user_id')
        
        if not user_message:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        # Создаем уникальный ключ для пользователя и агента
        user_agent_key = f"{user_id}_{agent_id}"
        
        # Создаем ассистента если его еще нет
        if user_agent_key not in user_assistants:
            assistant_data = create_assistant(agent_character)
            if not assistant_data:
                return jsonify({'error': 'Не удалось создать ассистента'}), 500
            user_assistants[user_agent_key] = assistant_data['id']
        
        # Создаем тред если его еще нет
        if user_agent_key not in user_threads:
            thread_data = create_thread()
            if not thread_data:
                return jsonify({'error': 'Не удалось создать тред'}), 500
            user_threads[user_agent_key] = thread_data['id']
        
        assistant_id = user_assistants[user_agent_key]
        thread_id = user_threads[user_agent_key]
        
        # Отправляем сообщение в тред
        message_result = send_message_to_thread(thread_id, user_message)
        if not message_result:
            return jsonify({'error': 'Не удалось отправить сообщение'}), 500
        
        # Запускаем ассистента
        run_result = run_assistant(assistant_id, thread_id)
        if not run_result:
            return jsonify({'error': 'Не удалось запустить ассистента'}), 500
        
        run_id = run_result['id']
        
        # Ждем завершения и получаем результат
        import time
        max_attempts = 30
        for attempt in range(max_attempts):
            result = get_run_result(thread_id, run_id)
            if result and result.get('status') == 'completed':
                if 'result' in result and 'text' in result['result']:
                    ai_response = result['result']['text']
                    
                    return jsonify({
                        'success': True,
                        'response': ai_response,
                        'timestamp': data.get('timestamp')
                    })
                else:
                    return jsonify({'error': 'Пустой ответ от ассистента'}), 500
            elif result and result.get('status') == 'failed':
                return jsonify({'error': 'Ассистент не смог обработать запрос'}), 500
            
            time.sleep(1)
        
        return jsonify({'error': 'Превышено время ожидания ответа'}), 504
            
    except Exception as e:
        print(f"Неожиданная ошибка в chat_with_assistant: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@yandex_assistant_bp.route('/test', methods=['GET'])
@login_required
def test_yandex_assistant():
    """Тестовый эндпоинт для проверки работы Яндекс Assistant"""
    try:
        # Создаем тестового ассистента
        test_character = "Ты дружелюбный AI ассистент. Отвечай кратко и по делу."
        assistant_data = create_assistant(test_character)
        
        if not assistant_data:
            return jsonify({'success': False, 'error': 'Не удалось создать ассистента'}), 500
        
        # Создаем тред
        thread_data = create_thread()
        if not thread_data:
            return jsonify({'success': False, 'error': 'Не удалось создать тред'}), 500
        
        return jsonify({
            'success': True,
            'assistant_id': assistant_data['id'],
            'thread_id': thread_data['id'],
            'config': {
                'folder_id': YANDEX_ASSISTANT_CONFIG['folder_id']
            }
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

