from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import User
from .permissions import ensure_access_groups, sync_user_group


@receiver(post_migrate)
def create_access_groups(sender, **kwargs):
    if sender.name != "accounts":
        return
    ensure_access_groups()
    for user in User.objects.filter(is_superuser=False):
        sync_user_group(user)


@receiver(post_save, sender=User)
def setup_user_access(sender, instance, raw=False, **kwargs):
    if not raw:
        sync_user_group(instance)
