import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            from django.contrib.auth.models import User
            from .models import Chat, UserProfile

            query_params = self.scope['query_string'].decode()
            token = None
            for param in query_params.split('&'):
                if param.startswith('token='):
                    token = param.split('=')[1]
                    break

            if not token:
                await self.close()
                return
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
            except jwt.InvalidTokenError:
                await self.close()
                return

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
                self.channel_name)

            await self.accept()
            print(f"WebSocket connected: {self.user.username} chat {self.chat_id}")

            previous_messages = await self.send_previous_messages()
            for message in previous_messages:
                await self.send(text_data=json.dumps(message))

        except Exception as e:
            print(f"Connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            from .models import Message, Notification

            text_data_json = json.loads(text_data)
            message_text = text_data_json['message']
            mentions = text_data_json.get('mentions', [])

            saved_message = await self.save_message(message_text, mentions)

            # Mention qilingan userlarga notification create qlish
            await self.create_notifications(saved_message, mentions)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_text,
                    'sender': self.user.username,
                    'sender_type': await self.get_user_type(self.user),
                    'timestamp': saved_message.timestamp.isoformat(),
                    'mentions': mentions
                }
            )

        except Exception as e:
            print(f"Receive error: {e}")
            await self.send(text_data=json.dumps({
                'error': 'Xatolik yuz berdi',
                'details': str(e)
            }))

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps({'message': event['message'], 'sender': event['sender'], 'sender_type': event['sender_type'],
                'timestamp': event['timestamp'],
                'mentions': event['mentions']
            }))
        except Exception as e:
            print(f"Chat message error: {e}")

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth.models import User
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_type(self, user):
        from .models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
            return profile.user_type
        except UserProfile.DoesNotExist:
            return 'user'

    @database_sync_to_async
    def get_chat(self, chat_id):
        from .models import Chat
        try:
            return Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def has_access_to_chat(self):
        from .models import UserProfile
        try:
            profile = UserProfile.objects.get(user=self.user)
            user_type = profile.user_type
        except UserProfile.DoesNotExist:
            user_type = "user"

        # Adminlar barcha chatlarga kira oladi
        # if user_type in ['visa_admin', 'master_admin']:
        #     return True

        return self.chat.user == self.user

    @database_sync_to_async
    def save_message(self, message, mentions):
        from .models import Message
        from django.contrib.auth.models import User

        message_obj = Message.objects.create( chat=self.chat, sender=self.user, content=message)

        # mention qilingan user qo'shish
        for username in mentions:
            try:
                user = User.objects.get(username=username)
                message_obj.mentions.add(user)
            except User.DoesNotExist:
                pass

        return message_obj

    @database_sync_to_async
    def create_notifications(self, message, mentions):
        from .models import Notification, UserProfile
        from django.contrib.auth.models import User

        for username in mentions:
            try:
                user = User.objects.get(username=username)
                user_profile = UserProfile.objects.get(user=user)

                Notification.objects.create(
                    user_profile=user_profile,
                    message=message,
                    chat_id=message.chat.id
                )
                print(f"Notification create: {username}uchun, chat: {message.chat.id}")
            except User.DoesNotExist:
                print(f"User topilmadi  {username}")

            except Exception as e:
                print(f"Notification : {e}")

    @database_sync_to_async
    def send_previous_messages(self):
        from .models import Message, UserProfile

        messages = Message.objects.filter(chat=self.chat).order_by('timestamp')[:50]

        previous_messages = []
        for message in messages:
            try:
                sender_profile = UserProfile.objects.get(user=message.sender)
                sender_type = sender_profile.user_type
            except UserProfile.DoesNotExist:
                sender_type = 'user'

            previous_messages.append({
                'message': message.content,
                'sender': message.sender.username,
                'sender_type': sender_type,
                'timestamp': message.timestamp.isoformat(),
                'mentions': [user.username for user in message.mentions.all()]
            })

        return previous_messages