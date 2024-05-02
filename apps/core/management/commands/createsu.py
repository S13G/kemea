from decouple import config
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a superuser.'

    def handle(self, *args, **options):
        admin_email = config('ADMIN_EMAIL')
        admin_password = config('ADMIN_PASSWORD')

        if not User.objects.filter(email=admin_email).exists():
            user = User.objects.create_superuser(
                email=admin_email,
                password=admin_password
            )
            self.stdout.write('Superuser has been created.')
        else:
            self.stderr.write("Superuser already exists.")
