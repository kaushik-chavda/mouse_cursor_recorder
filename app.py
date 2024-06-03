import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import cv2
from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit
import sqlite3
import os
import base64
from loguru import logger
import uuid

app = Flask(__name__)
socketio = SocketIO(app)

DB_PATH = 'mouse_tracker.db'
IMAGE_DIR = 'images'

# Dictionary to store client IDs
client_ids = {}


def initialize_database() -> None:
    """Initialize the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS mouse_tracker
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT, x INTEGER, y INTEGER, img_path TEXT)''')
    logger.info("Initialized database successfully")


def save_mouse_movement(client_id: str, x: int, y: int, img_path: str) -> None:
    """Save mouse movement data to the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO mouse_tracker (client_id, x, y, img_path) VALUES (?, ?, ?, ?)",
                         (client_id, x, y, img_path))
        logger.info("Saved mouse data (client_id={}, x={}, y={}, img_path={})", client_id, x, y, img_path)
    except sqlite3.Error as e:
        logger.error("Error saving mouse data: {}", e)


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    client_id = str(uuid.uuid4())
    client_ids[request.sid] = client_id
    emit('client_id', {'client_id': client_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    client_ids.pop(request.sid, None)


@socketio.on('mouse_event')
def handle_mouse_movement_event(data: dict) -> None:
    """Handle mouse movement events from the client."""
    try:
        client_id = client_ids.get(request.sid)
        if client_id is None:
            logger.error("Unknown client ID for WebSocket SID: {}", request.sid)
            return

        x, y = data['x'], data['y']
        img_path = None
        if data['button_pressed']:
            img_path = asyncio.run(capture_and_save_image_async(client_id, x, y))
        save_mouse_movement(client_id, x, y, img_path)
        emit('new_image', {'x': x, 'y': y, 'img_path': img_path}, broadcast=True)
        logger.info("Handled mouse event (client_id={}, x={}, y={}, button_pressed={}, img_path={})", client_id, x, y,
                    data['button_pressed'],
                    img_path)
    except Exception as e:
        logger.error("Error handling mouse event: {}", e)


async def capture_and_save_image_async(client_id: str, x: int, y: int) -> str:
    """Asynchronously capture and save an image."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, lambda: capture_image(client_id, x, y))


def capture_image(client_id: str, x: int, y: int) -> str:
    """Capture an image from the webcam and save it to a file."""
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if ret:
            os.makedirs(IMAGE_DIR, exist_ok=True)
            encoded_x = base64.urlsafe_b64encode(str(x).encode()).decode()
            encoded_y = base64.urlsafe_b64encode(str(y).encode()).decode()
            img_path = os.path.join(IMAGE_DIR, f'img_{client_id}_{encoded_x}_{encoded_y}.jpg')
            cv2.imwrite(img_path, frame)
            logger.info("Captured image at path {}", img_path)
            return img_path
    except Exception as e:
        logger.error("Error capturing image: {}", e)
    return ''


@app.route('/')
def render_index_page() -> str:
    """Render the index.html template."""
    return render_template('index.html')


@app.route('/images/<path:filename>')
def download_file(filename: str) -> Any:
    """Serve the saved images."""
    return send_from_directory('images', filename)


@app.route('/images')
def view_saved_images() -> str:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT x, y, img_path FROM mouse_tracker WHERE img_path IS NOT NULL")
            data = cursor.fetchall()
        logger.info("Retrieved {} images from the database", len(data))
        return render_template('captured_data.html', data=data)
    except sqlite3.Error as e:
        logger.error("Error fetching data from database: {}", e)
        return "An error occurred while fetching data from the database."


if __name__ == '__main__':
    initialize_database()
    socketio.run(app, debug=True)
