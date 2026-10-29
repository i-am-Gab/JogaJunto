from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    phone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    role = models.CharField("Perfil", max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username


@receiver(post_save, sender=User)
def set_staff_status(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        instance.is_staff = True
        instance.save()
