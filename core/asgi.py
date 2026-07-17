import os

import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import socketio

import chat.socket_handlers as socket_handlers_module
from chat.socket_handlers import register_socket_handlers

django_asgi_app = get_asgi_application()

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False,
)
socket_handlers_module.sio = sio
register_socket_handlers(sio)

application = socketio.ASGIApp(
    sio,
    django_asgi_app,
    socketio_path='socket.io',
)
