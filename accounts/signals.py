from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import ROLE_PARTICIPANT, User
from .permissions import ensure_access_groups, sync_user_group


@receiver(post_migrate)
def create_access_groups(sender, **kwargs):
    if sender.name != "accounts":
        return
    ensure_access_groups()
    for user in User.objects.filter(is_superuser=False):
        if not user.groups.exists():
            sync_user_group(user)


@receiver(post_save, sender=User)
def setup_new_user_access(sender, instance, created, **kwargs):
    if not created or instance.is_superuser:
        return

    updates = {}
    if not instance.is_staff:
        updates["is_staff"] = True
    if not instance.role:
        updates["role"] = ROLE_PARTICIPANT

    if updates:
        sender.objects.filter(pk=instance.pk).update(**updates)
        for field, value in updates.items():
            setattr(instance, field, value)

    sync_user_group(instance)
