from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone


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
    latitude = models.DecimalField(
        "Latitude", max_digits=11, decimal_places=8, blank=True, null=True
    )
    longitude = models.DecimalField(
        "Longitude", max_digits=11, decimal_places=8, blank=True, null=True
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
        related_name="organized_activities", verbose_name="Organizador",
    )
    modality = models.ForeignKey(
        Modality, on_delete=models.PROTECT, related_name="activities", verbose_name="Modalidade"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name="activities", verbose_name="Local"
    )

    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descrição")
    starts_at = models.DateTimeField("Início")
    ends_at = models.DateTimeField("Término")
    max_participants = models.PositiveIntegerField(
        "Limite de Participantes", validators=[MinValueValidator(1, message="Informe pelo menos uma vaga.")]
    )
    price = models.DecimalField(
        "Valor", max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0, message="O valor não pode ser negativo.")],
    )
    confirmation_deadline = models.DateTimeField(
        "Prazo de Confirmação",
        help_text="Data e horário limite para confirmar a participação. Deve ser anterior ao início da atividade.",
    )
    registration_type = models.CharField(
        "Tipo de Inscrição", max_length=20, choices=REGISTRATION_CHOICES, default="AUTO"
    )
    status = models.CharField(
        "Status", max_length=20, choices=STATUS_CHOICES, default="DRAFT"
    )

    created_at = models.DateTimeField("Criada em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizada em", auto_now=True)

    @property
    def accepts_registrations(self):
        now = timezone.now()
        return self.status == "PUBLISHED" and now < self.starts_at and now < self.confirmation_deadline

    def clean(self):
        super().clean()
        errors = {}
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "O término deve ser depois do início da atividade. Confira a data e o horário."
        if self.starts_at and self.confirmation_deadline and self.confirmation_deadline >= self.starts_at:
            errors["confirmation_deadline"] = "O prazo de confirmação deve ser antes do início da atividade. Confira a data e o horário."
        if errors:
            raise ValidationError(errors)

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
