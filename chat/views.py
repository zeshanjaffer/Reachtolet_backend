import logging

from asgiref.sync import async_to_sync
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.responses import action_response

from .serializers import ChatMessageCreateSerializer
from .services import (
    ChatError,
    create_message,
    get_room_for_user,
    serialize_message,
    notify_recipient_of_chat_message,
)
from . import socket_handlers

logger = logging.getLogger(__name__)


class ChatMessageListCreateView(APIView):
    """
    REST is attachment-only.
    Text messages must use Socket.IO `send_message`.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['post', 'options', 'head']

    def post(self, request, room_id):
        try:
            room = get_room_for_user(room_id, request.user)
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = []
        for key, file_obj in request.FILES.items():
            if key.startswith('attachment') or key.startswith('file'):
                files.append(file_obj)

        if not files:
            return action_response(
                'At least one attachment file is required. '
                'Use Socket.IO send_message for text-only messages.',
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            message, _attachment_rows = create_message(
                room,
                request.user,
                body=serializer.validated_data.get('body', ''),
                files=files,
                request=request,
            )
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        payload = serialize_message(message, request)
        _broadcast_new_message(room, request.user, payload)
        try:
            notify_recipient_of_chat_message(room, request.user, message)
        except Exception as exc:
            logger.warning('Chat inbox notification failed: %s', exc)

        return Response(
            {
                'status_code': status.HTTP_201_CREATED,
                'message': 'Message sent',
                'message_data': payload,
            },
            status=status.HTTP_201_CREATED,
        )


def _broadcast_new_message(room, sender, payload):
    if socket_handlers.sio is None:
        return
    try:
        other = room.other_user(sender)
        async_to_sync(socket_handlers.emit_new_message)(
            room.id,
            payload,
            recipient=other,
            room=room,
            sender=sender,
        )
    except Exception as exc:
        logger.warning('Socket broadcast failed: %s', exc)
