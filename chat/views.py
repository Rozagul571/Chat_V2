import jwt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from .models import Chat, UserProfile
from .serializers import UserSerializer
from .authentication import JWTAuthentication  # Yangi authentication klass


@api_view(['POST'])
@authentication_classes([])  # Login uchun authentication kerak emas
@permission_classes([])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user is not None:
        # JWT token yaratish
        token = jwt.encode(
            {'user_id': user.id},
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        return Response({
            'status': 'success',
            'user_id': user.id,
            'username': user.username,
            'token': token
        })
    else:
        return Response({
            'status': 'error',
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])  # Faqat JWT authentication
@permission_classes([permissions.IsAuthenticated])
def get_or_create_chat(request):
    # User uchun chat olish yoki yaratish
    user = request.user

    try:
        chat = Chat.objects.get(user=user)
    except Chat.DoesNotExist:
        chat = Chat.objects.create(user=user)

    return Response({
        'status': 'success',
        'chat_id': str(chat.id)
    })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([permissions.IsAuthenticated])
def get_chat_messages(request, chat_id):
    # Chat xabarlarini olish
    try:
        chat = Chat.objects.get(id=chat_id)

        # Kirish huquqini tekshirish
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.user_type not in ['visa_admin', 'master_admin'] and chat.user != request.user:
                return Response({
                    'status': 'error',
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
        except UserProfile.DoesNotExist:
            # Agar profil topilmasa, oddiy foydalanuvchi deb hisoblaymiz
            if chat.user != request.user:
                return Response({
                    'status': 'error',
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)

        messages = chat.messages.all().order_by('timestamp')
        messages_data = []

        for message in messages:
            # Har bir xabarning sender_type ni olish
            try:
                sender_profile = UserProfile.objects.get(user=message.sender)
                sender_type = sender_profile.user_type
            except UserProfile.DoesNotExist:
                sender_type = 'user'

            messages_data.append({
                'id': message.id,
                'sender': message.sender.username,
                'sender_type': sender_type,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'mentions': [user.username for user in message.mentions.all()]
            })

        return Response({
            'status': 'success',
            'messages': messages_data
        })

    except Chat.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Chat not found'
        }, status=status.HTTP_404_NOT_FOUND)


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]