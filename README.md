# Twinby дрон 🚁

**Проект Фабрика персонажей**<br>
Задание: создать интерактивный конструктор AI персонажей, с которыми можно общаться

## Основная идея
Дрон-ассистент, с которым можно общаться и ходить на свидания, используя для общения с живым человеком или AI-агентом 

---

## **Frontend** <br>
Фреймворк: React <br>
Сборщик/Сервер разработки: Vite<br>
Язык: JavaScript/TypeScript.<br><br>


## **Backend**<br>
Язык: Python.<br>
Веб-фреймворк: Flas<br>
Внешние API: Интеграция с сервисами Яндекса: yandex_gpt.py<br>
(для генерации текста или ответов) и yandex_assistant.py (для голосовых ассистентов или других интерактивных функций).<br><br>

## **Структура директории:**

```
ai-call-app-minimal/
├── public/             # Статические файлы (index.html, favicon.ico и т.д.)
├── src/                # Исходный код приложения
│   ├── assets/         # Изображения, шрифты, иконки
│   ├── components/     # Переиспользуемые UI-компоненты (кнопки, карточки и т.д.)
│   ├── pages/          # Страницы приложения (главная, настройки, чат и т.д.)
│   ├── services/       # Модули для взаимодействия с API бэкенда
│   ├── utils/          # Вспомогательные утилиты и функции
│   ├── App.jsx         # Основной компонент приложения
│   ├── main.jsx        # Точка входа в приложение (рендеринг React-приложения)
│   └── index.css       # Глобальные стили
├── package.json        # Описание проекта и его зависимостей
├── package-lock.json   # Зафиксированные версии зависимостей
├── vite.config.js      # Конфигурация Vite
└── README.md           # Документация по фронтенду
```

**Взаимодействие:** Фронтенд отправляет асинхронные HTTP-запросы (GET, POST и т.д.) к API бэкенда для получения данных (например, списка AI агентов, истории чатов) и отправки команд (например, создание нового AI агента, отправка сообщения).

---
# Clover Drone Web Server

Web server for controlling COEX Clover drone with character-based interactions.

## Prerequisites

- COEX Clover drone with ROS setup
- Python 3.7 or higher
- ROS environment properly configured

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the drone's ROS environment is sourced:
```bash
source /opt/ros/noetic/setup.bash  # Adjust for your ROS version
source ~/catkin_ws/devel/setup.bash
```

## Running the Server

1. Start the server:
```bash
python3 drone/tw_drone_webserver.py
```

The server will run on `http://localhost:3001`.

## API Endpoints

### Takeoff
```http
POST /api/drone/takeoff
```
Initiates drone takeoff to 1.5 meters height.

### Turn
```http
POST /api/drone/turn?character={character}
```
Turns drone to show specific character side.

Available characters:
- `business` - Front
- `creative` - Back
- `mystery` - Left side
- `innovation` - Right side
- `default` - Front

### Audio (Placeholder)
```http
POST /api/drone/audio
```
Placeholder for future audio streaming implementation.

## Safety Notes

- Always ensure proper safety measures when operating the drone
- Keep clear space around the drone during operation
- Have a physical remote control ready for manual override if needed