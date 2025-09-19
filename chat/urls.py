from django.urls import path
from .views import login_view, get_or_create_chat, get_chat_messages, UserList

urlpatterns = [
    path('login/', login_view, name='login'),
    path('chat/', get_or_create_chat, name='get_or_create_chat'),
    path('chat/<uuid:chat_id>/messages/', get_chat_messages, name='get_chat_messages'),
    path('users/', UserList.as_view(), name='user_list'),
]