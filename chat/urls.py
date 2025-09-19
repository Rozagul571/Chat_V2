from django.urls import path
from .views import LoginView, ChatView, ChatMessagesView, UserListView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('chat/', ChatView.as_view(), name='get_chat'),
    path('chat/<uuid:chat_id>/messages/', ChatMessagesView.as_view(), name='get_chat_messages'),
    path('users/', UserListView.as_view(), name='user_list'),
]
