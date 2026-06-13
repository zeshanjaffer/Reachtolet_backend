from django.urls import path

from .views import (
    ChatMarkDeliveredView,
    ChatMarkReadView,
    ChatMessageListCreateView,
    ChatRoomByBillboardView,
    ChatRoomDetailView,
    ChatRoomListCreateView,
    ChatUnreadSummaryView,
)

urlpatterns = [
    path('unread/', ChatUnreadSummaryView.as_view(), name='chat-unread-summary'),
    path('rooms/', ChatRoomListCreateView.as_view(), name='chat-room-list-create'),
    path('rooms/by-billboard/<int:billboard_id>/', ChatRoomByBillboardView.as_view(), name='chat-room-by-billboard'),
    path('rooms/<int:room_id>/', ChatRoomDetailView.as_view(), name='chat-room-detail'),
    path('rooms/<int:room_id>/messages/', ChatMessageListCreateView.as_view(), name='chat-message-list-create'),
    path('rooms/<int:room_id>/read/', ChatMarkReadView.as_view(), name='chat-mark-read'),
    path(
        'rooms/<int:room_id>/messages/<int:message_id>/delivered/',
        ChatMarkDeliveredView.as_view(),
        name='chat-mark-delivered',
    ),
]
