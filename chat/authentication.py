import jwt
from django.conf import settings
from rest_framework import authentication, exceptions


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        from django.contrib.auth.models import User

        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            if not auth_header.startswith('Bearer '):
                raise exceptions.AuthenticationFailed('Invalid authorization header')

            token = auth_header.split(' ')[1]

            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')

            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid token')

            user = User.objects.get(id=user_id)

            return (user, None)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')