from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chat.models import UserProfile


class Command(BaseCommand):
    help = 'Create default Visa, Mastercard admins and a normal user'

    def handle(self, *args, **kwargs):
        users = [
            {'username': 'visa', 'password': 'visa123', 'user_type': 'visa_admin'},
            {'username': 'mastercard', 'password': 'mc123', 'user_type': 'master_admin'},
            {'username': 'user1', 'password': 'user123', 'user_type': 'user'},
        ]

        for u in users:
            if not User.objects.filter(username=u['username']).exists():
                user = User.objects.create_user(
                    username=u['username'],
                    password=u['password'],
                    is_active=True,
                    is_staff=True if u['user_type'] != 'user' else False
                )
                UserProfile.objects.create(user=user, user_type=u['user_type'])
                self.stdout.write(self.style.SUCCESS(f"Created {u['username']} ({u['user_type']})"))
            else:
                self.stdout.write(self.style.WARNING(f"{u['username']} already exists"))
