import jwt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth.models import User
from .models import Chat, UserProfile
from .serializers import UserSerializer
from .authentication import JWTAuthentication


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            token = jwt.encode(
                {'user_id': user.id},
                settings.SECRET_KEY,
                algorithm='HS256'
            )
            return Response({'status': 'success', 'user_id': user.id,'username': user.username,
                'token': token})

        return Response({'status': 'error',
            'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



class ChatView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        chat, _ = Chat.objects.get_or_create(user=request.user)
        return Response({'chat_id': str(chat.id)})


class ChatMessagesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)

            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if user_profile.user_type not in ['visa_admin', 'master_admin'] and chat.user != request.user:
                    return Response({'status': 'error', 'message': 'Access denied'}, status=403)
            except UserProfile.DoesNotExist:
                if chat.user != request.user:
                    return Response({'status': 'error', 'message': 'Access denied'}, status=403)

            messages = chat.messages.all().order_by('timestamp')
            messages_data = []
            for message in messages:
                try:
                    sender_profile = UserProfile.objects.get(user=message.sender)
                    sender_type = sender_profile.user_type
                except UserProfile.DoesNotExist:
                    sender_type = 'user'

                messages_data.append({'id': message.id,
                    'sender': message.sender.username, 'sender_type': sender_type,
                    'content': message.content, 'timestamp': message.timestamp.isoformat(),
                    'mentions': [user.username for user in message.mentions.all()]})

            return Response({'status': 'success', 'messages': messages_data})

        except Chat.DoesNotExist:
            return Response({'status': 'error', 'message': 'Chat not found'}, status=404)


class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
