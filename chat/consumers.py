import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_params = self.scope['query_string'].decode()
        token = None
        for param in query_params.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break

        if not token:
            await self.close()
            return

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        self.user = await self.get_user(user_id)
        if not self.user:
            await self.close()
            return

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat = await self.get_chat(self.chat_id)
        if not self.chat:
            await self.close()
            return

        if not await self.has_access_to_chat():
            await self.close()
            return

        self.room_group_name = f'chat_{self.chat_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        # print(f"conected: {self.user.username} to chat {self.chat_id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        mentions = data.get('mentions', [])

        saved_message = await self.save_message(message, mentions)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message',
                'message': message,
                'sender': self.user.username,
                'sender_type': await self.get_user_type(self.user),
                'timestamp': saved_message.timestamp.isoformat(),
                'mentions': mentions
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(id=user_id).first()

    @database_sync_to_async
    def get_user_type(self, user):
        from chat.models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        return profile.user_type if profile else 'user'

    @database_sync_to_async
    def get_chat(self, chat_id):
        from chat.models import Chat
        return Chat.objects.filter(id=chat_id).first()

    @database_sync_to_async
    def has_access_to_chat(self):
        from .models import UserProfile
        profile = UserProfile.objects.filter(user=self.user).first()
        user_type = profile.user_type if profile else 'user'
        if user_type in ['visa_admin', 'master_admin']:
            return True
        return self.chat.user == self.user

    @database_sync_to_async
    def save_message(self, message, mentions):
        from django.contrib.auth import get_user_model
        from .models import Message
        User = get_user_model()

        msg = Message.objects.create(
            chat=self.chat,
            sender=self.user,
            content=message
        )

        users = User.objects.filter(username__in=mentions)
        msg.mentions.add(*users)
        return msg
