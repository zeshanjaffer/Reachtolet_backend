from django.conf import settings
from django.db import models
from django.utils import timezone


class ChatRoom(models.Model):
    """One chat thread per advertiser + billboard (OLX-style). Media owner = billboard owner."""

    billboard = models.ForeignKey(
        'billboards.Billboard',
        on_delete=models.CASCADE,
        related_name='chat_rooms',
    )
    advertiser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='advertiser_chat_rooms',
    )
    media_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_owner_chat_rooms',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['billboard', 'advertiser'],
                name='uniq_chat_room_billboard_advertiser',
            ),
        ]
        indexes = [
            models.Index(fields=['advertiser', '-updated_at']),
            models.Index(fields=['media_owner', '-updated_at']),
        ]

    def __str__(self):
        return f'Room {self.pk} — billboard {self.billboard_id}'

    def other_user(self, user):
        if user_id := getattr(user, 'id', None):
            if user_id == self.advertiser_id:
                return self.media_owner
            if user_id == self.media_owner_id:
                return self.advertiser
        return None

    def is_participant(self, user):
        if not user or not user.is_authenticated:
            return False
        return user.id in (self.advertiser_id, self.media_owner_id)


class ChatRoomParticipant(models.Model):
    """Per-user read cursor and typing is socket-only (not stored)."""

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_participations')
    last_read_message = models.ForeignKey(
        'ChatMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['room', 'user'], name='uniq_chat_participant_room_user'),
        ]

    def __str__(self):
        return f'Participant user={self.user_id} room={self.room_id}'


class ChatMessage(models.Model):
    MESSAGE_TYPE_TEXT = 'text'
    MESSAGE_TYPE_ATTACHMENT = 'attachment'
    MESSAGE_TYPE_MIXED = 'mixed'
    MESSAGE_TYPE_CHOICES = [
        (MESSAGE_TYPE_TEXT, 'Text'),
        (MESSAGE_TYPE_ATTACHMENT, 'Attachment'),
        (MESSAGE_TYPE_MIXED, 'Text with attachment'),
    ]

    STATUS_SENT = 'sent'
    STATUS_DELIVERED = 'delivered'
    STATUS_SEEN = 'seen'
    STATUS_CHOICES = [
        (STATUS_SENT, 'Sent'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_SEEN, 'Seen'),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages_sent')
    body = models.TextField(blank=True, default='')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default=MESSAGE_TYPE_TEXT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SENT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['room', '-created_at']),
        ]

    def __str__(self):
        return f'Message {self.pk} in room {self.room_id}'


class ChatAttachment(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/%Y/%m/')
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True, default='')
    file_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.original_name
