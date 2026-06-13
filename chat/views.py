
import logging

from asgiref.sync import async_to_sync
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination
from core.responses import action_response

from .models import ChatMessage, ChatRoom
from .serializers import ChatMarkReadSerializer, ChatMessageCreateSerializer, ChatRoomCreateSerializer
from .services import (
    ChatError,
    create_message,
    get_or_create_room,
    get_unread_summary,
    get_room_for_user,
    list_rooms_for_user,
    mark_message_delivered,
    mark_messages_seen,
    serialize_message,
    serialize_room,
)
from . import socket_handlers

logger = logging.getLogger(__name__)


class ChatUnreadSummaryView(APIView):
    """Total unread badge for advertiser and media owner (same logic both sides)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        summary = get_unread_summary(request.user)
        return Response(
            {
                'status_code': status.HTTP_200_OK,
                **summary,
            },
            status=status.HTTP_200_OK,
        )


class ChatRoomListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        rooms = list_rooms_for_user(request.user).select_related(
            'billboard', 'advertiser', 'media_owner'
        )
        paginator = CustomPagination()
        page = paginator.paginate_queryset(rooms, request)
        data = [serialize_room(r, request.user, request) for r in page]
        return paginator.get_paginated_response(data)

    def post(self, request):
        """Advertiser starts chat from billboard detail (get-or-create room)."""
        serializer = ChatRoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            room, created = get_or_create_room(
                serializer.validated_data['billboard_id'],
                request.user,
            )
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        payload = serialize_room(room, request.user, request)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        message = 'Chat room created' if created else 'Chat room already exists'
        return Response(
            {'status_code': code, 'message': message, 'room': payload},
            status=code,
        )


class ChatRoomByBillboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, billboard_id):
        if request.user.user_type != 'advertiser':
            return action_response(
                'Only advertisers can open chat from a billboard detail screen.',
                status.HTTP_403_FORBIDDEN,
            )
        try:
            room, created = get_or_create_room(billboard_id, request.user)
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        payload = serialize_room(room, request.user, request)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        message = 'Chat room created' if created else 'Chat room retrieved'
        return Response(
            {'status_code': code, 'message': message, 'room': payload},
            status=code,
        )


class ChatRoomDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, room_id):
        try:
            room = get_room_for_user(room_id, request.user)
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)
        return Response(serialize_room(room, request.user, request))


class ChatMessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, room_id):
        try:
            room = get_room_for_user(room_id, request.user)
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        qs = (
            ChatMessage.objects.filter(room=room)
            .select_related('sender')
            .prefetch_related('attachments')
            .order_by('-created_at')
        )
        paginator = CustomPagination()
        page = paginator.paginate_queryset(qs, request)
        data = [serialize_message(m, request) for m in reversed(list(page))]
        return paginator.get_paginated_response(data)

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

        try:
            message, attachment_rows = create_message(
                room,
                request.user,
                body=serializer.validated_data.get('body', ''),
                files=files,
                request=request,
            )
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        payload = serialize_message(message, request)
        _broadcast_new_message(room.id, payload)

        return Response(
            {
                'status_code': status.HTTP_201_CREATED,
                'message': 'Message sent',
                'message_data': payload,
            },
            status=status.HTTP_201_CREATED,
        )


class ChatMarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = get_room_for_user(room_id, request.user)
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        serializer = ChatMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            last_message = mark_messages_seen(
                room,
                request.user,
                serializer.validated_data['message_id'],
            )
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        _broadcast_messages_seen(room.id, request.user.id, last_message.id)

        return Response(
            {
                'status_code': status.HTTP_200_OK,
                'message': 'Messages marked as read',
                'message_id': last_message.id,
                'status': ChatMessage.STATUS_SEEN,
            },
            status=status.HTTP_200_OK,
        )


class ChatMarkDeliveredView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_id, message_id):
        try:
            room = get_room_for_user(room_id, request.user)
        except ChatError as exc:
            return action_response(exc.message, exc.status_code)

        try:
            message = ChatMessage.objects.get(pk=message_id, room=room)
        except ChatMessage.DoesNotExist:
            return action_response('Message not found.', status.HTTP_404_NOT_FOUND)

        message = mark_message_delivered(message, request.user)
        _broadcast_message_delivered(room.id, request.user.id, message.id, message.status)

        return Response(
            {
                'status_code': status.HTTP_200_OK,
                'message_id': message.id,
                'status': message.status,
            },
            status=status.HTTP_200_OK,
        )


def _broadcast_new_message(room_id, payload):
    if socket_handlers.sio is None:
        return
    try:
        async_to_sync(socket_handlers.emit_new_message)(room_id, payload)
    except Exception as exc:
        logger.warning('Socket broadcast failed: %s', exc)


def _broadcast_message_delivered(room_id, user_id, message_id, msg_status):
    if socket_handlers.sio is None:
        return
    try:
        async_to_sync(socket_handlers.sio.emit)(
            'message_delivered',
            {
                'room_id': room_id,
                'message_id': message_id,
                'user_id': user_id,
                'status': msg_status,
            },
            room=socket_handlers.room_channel(room_id),
        )
    except Exception as exc:
        logger.warning('Socket delivered broadcast failed: %s', exc)


def _broadcast_messages_seen(room_id, user_id, message_id):
    if socket_handlers.sio is None:
        return
    try:
        async_to_sync(socket_handlers.sio.emit)(
            'messages_seen',
            {
                'room_id': room_id,
                'message_id': message_id,
                'user_id': user_id,
                'status': ChatMessage.STATUS_SEEN,
            },
            room=socket_handlers.room_channel(room_id),
        )
    except Exception as exc:
        logger.warning('Socket seen broadcast failed: %s', exc)
