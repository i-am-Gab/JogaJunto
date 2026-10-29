from django.db import models
from django.conf import settings


class Registration(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pendente"),
        ("APPROVED", "Aprovada"),
        ("REJECTED", "Rejeitada"),
        ("WAITLIST", "Lista de Espera"),
        ("CANCELED", "Cancelada"),
    )

    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.CASCADE, related_name="registrations"
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registrations"
    )
    status = models.CharField(
        "Status", max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )

    requested_at = models.DateTimeField("Solicitado em", auto_now_add=True)
    decided_at = models.DateTimeField("Decidido em", blank=True, null=True)
    confirmed_at = models.DateTimeField("Confirmado em", blank=True, null=True)
    cancelled_at = models.DateTimeField("Cancelado em", blank=True, null=True)
    organizer_notes = models.TextField("Notas do Organizador", blank=True, null=True)

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "participant"],
                name="unique_registration_per_participant",
            )
        ]

    def __str__(self):
        return f"{self.participant.username} -> {self.activity.title}"


class Payment(models.Model):
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name="payment"
    )
    amount = models.DecimalField("Valor Pago", max_digits=10, decimal_places=2)
    status = models.CharField("Status", max_length=50)
    method = models.CharField("Método de Pagamento", max_length=50)
    paid_at = models.DateTimeField("Pago em", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"

    def __str__(self):
        return f"Pagamento: {self.registration}"


class Attendance(models.Model):
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name="attendance"
    )
    attended = models.BooleanField("Presente", default=False)
    check_in_at = models.DateTimeField("Check-in em", blank=True, null=True)
    notes = models.TextField("Observações", blank=True, null=True)

    class Meta:
        verbose_name = "Presença"
        verbose_name_plural = "Presenças"

    def __str__(self):
        return f"Presença: {self.registration}"
