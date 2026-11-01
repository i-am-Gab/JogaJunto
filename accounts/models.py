from django.contrib.auth.models import AbstractUser
from django.db import models


ROLE_PARTICIPANT = "participante"
ROLE_ORGANIZER = "organizador"

ROLE_CHOICES = (
    (ROLE_PARTICIPANT, "Participante"),
    (ROLE_ORGANIZER, "Organizador"),
)

GROUP_PARTICIPANT = "Participante"
GROUP_ORGANIZER = "Organizador"


class User(AbstractUser):
    phone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    role = models.CharField(
        "Perfil",
        max_length=50,
        choices=ROLE_CHOICES,
        default=ROLE_PARTICIPANT,
        blank=True,
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.get_full_name() or self.username

    def has_organizer_group(self):
        if self.is_superuser:
            return True
        return self.groups.filter(name=GROUP_ORGANIZER).exists()
