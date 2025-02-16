from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Creates a default employee user if none exists'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(user_type='EMPLOYEE').exists():
            User.objects.create_user(
                username='default_stylist',
                email='stylist@example.com',
                password='defaultpass123',
                user_type='EMPLOYEE'
            )
            self.stdout.write(self.style.SUCCESS('Successfully created default employee user')) 