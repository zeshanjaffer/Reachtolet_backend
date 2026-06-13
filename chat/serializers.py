from rest_framework import serializers

from .models import ChatMessage, ChatRoom


class ChatRoomCreateSerializer(serializers.Serializer):
    billboard_id = serializers.IntegerField()


class ChatMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(required=False, allow_blank=True, default='')


class ChatMarkReadSerializer(serializers.Serializer):
    message_id = serializers.IntegerField()
