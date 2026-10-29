from django.db import models
from django.conf import settings


class Modality(models.Model):
    name = models.CharField("Nome", max_length=100, unique=True)
    description = models.TextField("Descrição", blank=True, null=True)
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Modalidade"
        verbose_name_plural = "Modalidades"

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField("Nome do Local", max_length=150)
    street = models.CharField("Rua", max_length=150)
    number = models.CharField("Número", max_length=20, blank=True, null=True)
    neighborhood = models.CharField("Bairro", max_length=100)
    city = models.CharField("Cidade", max_length=100)
    state = models.CharField("Estado", max_length=2)
    zip_code = models.CharField("CEP", max_length=20)
    complement = models.CharField("Complemento", max_length=150, blank=True, null=True)
    reference_point = models.CharField(
        "Ponto de Referência", max_length=150, blank=True, null=True
    )

    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locais"

    def __str__(self):
        return f"{self.name} - {self.city}/{self.state}"


class Activity(models.Model):
    REGISTRATION_CHOICES = (("AUTO", "Automática"), ("MANUAL", "Mediante Aprovação"))
    STATUS_CHOICES = (
        ("DRAFT", "Rascunho"),
        ("PUBLISHED", "Publicada"),
        ("CANCELED", "Cancelada"),
        ("FINISHED", "Finalizada"),
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_activities",
    )
    modality = models.ForeignKey(
        Modality, on_delete=models.PROTECT, related_name="activities"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name="activities"
    )

    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descrição")
    starts_at = models.DateTimeField("Início")
    ends_at = models.DateTimeField("Término")
    max_participants = models.PositiveIntegerField("Limite de Participantes")
    price = models.DecimalField("Valor", max_digits=10, decimal_places=2, default=0.00)
    confirmation_deadline = models.DateTimeField("Prazo de Confirmação")
    registration_type = models.CharField(
        "Tipo de Inscrição", max_length=20, choices=REGISTRATION_CHOICES, default="AUTO"
    )
    status = models.CharField(
        "Status", max_length=20, choices=STATUS_CHOICES, default="DRAFT"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_participants__gt=0),
                name="check_max_participants_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0), name="check_price_non_negative"
            ),
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F("starts_at")),
                name="check_ends_after_starts",
            ),
            models.CheckConstraint(
                condition=models.Q(confirmation_deadline__lt=models.F("starts_at")),
                name="check_deadline_before_starts",
            ),
        ]

    def __str__(self):
        return self.title
