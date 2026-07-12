from django.urls import path

from .views import ChatMessageListCreateView

urlpatterns = [
    path(
        'rooms/<int:room_id>/messages/',
        ChatMessageListCreateView.as_view(),
        name='chat-message-list-create',
    ),
]
