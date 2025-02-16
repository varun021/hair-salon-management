from django.core.management.base import BaseCommand
from accounts.models import User, Profile

class Command(BaseCommand):
    help = 'Creates missing profiles for existing users'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} missing profiles'
            )
        ) 