from django.urls import path
from .views import (
    LoginView, ChatView, ChatMessagesView, UserListView,
    NotificationListView, NotificationReadView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('chat/<uuid:chat_id>/messages/', ChatMessagesView.as_view(), name='chat-messages'),
    path('users/', UserListView.as_view(), name='user-list'),

    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/read/', NotificationReadView.as_view(), name='notification-read'),
]
