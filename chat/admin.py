from django.contrib import admin

from .models import ChatAttachment, ChatMessage, ChatRoom, ChatRoomParticipant

admin.site.register(ChatRoom)
admin.site.register(ChatRoomParticipant)
admin.site.register(ChatMessage)
admin.site.register(ChatAttachment)
