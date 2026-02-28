from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Set superuser status"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--enable", action="store_true")
        parser.add_argument("--disable", action="store_true")

    def handle(self, *args, **options):
        User = get_user_model()

        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError("User not found")

        if options["enable"]:
            user.is_superuser = True
            user.is_staff = True

        if options["disable"]:
            user.is_superuser = False

        user.save()

        self.stdout.write(self.style.SUCCESS("User privileges updated"))