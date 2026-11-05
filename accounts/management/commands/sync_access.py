from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from accounts.permissions import ensure_access_groups, sync_user_group


class Command(BaseCommand):
    help = "Sincroniza acesso por perfil, preservando os superusuários."

    @transaction.atomic
    def handle(self, *args, **options):
        ensure_access_groups()
        users = User.objects.filter(is_superuser=False)
        count = users.count()
        for user in users:
            sync_user_group(user)
        self.stdout.write(self.style.SUCCESS(f"Acesso sincronizado: {count} usuário(s)."))
