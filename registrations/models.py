from django.db import models
from django.conf import settings
from django.utils import timezone


class Registration(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pendente"),
        ("APPROVED", "Aprovada"),
        ("REJECTED", "Rejeitada"),
        ("WAITLIST", "Lista de Espera"),
        ("CANCELED", "Cancelada"),
    )

    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.CASCADE, related_name="registrations", verbose_name="Atividade"
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registrations", verbose_name="Participante"
    )
    status = models.CharField(
        "Status", max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )

    requested_at = models.DateTimeField("Solicitado em", auto_now_add=True)
    decided_at = models.DateTimeField("Decidido em", blank=True, null=True)
    confirmed_at = models.DateTimeField("Confirmado em", blank=True, null=True)
    cancelled_at = models.DateTimeField("Cancelado em", blank=True, null=True)
    organizer_notes = models.TextField("Notas do Organizador", blank=True, null=True)
    seat_offered_at = models.DateTimeField("Vaga oferecida em", null=True, blank=True)

    @property
    def can_confirm_seat(self):
        return self.status == "WAITLIST" and self.seat_offered_at is not None and self.activity.accepts_registrations

    @property
    def can_cancel(self):
        return (
            self.status in ("PENDING", "APPROVED", "WAITLIST")
            and self.activity.status == "PUBLISHED"
            and self.activity.starts_at > timezone.now()
        )

    @property
    def can_resubscribe(self):
        return self.status == "CANCELED" and self.activity.accepts_registrations

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields is None or "status" in update_fields:
            previous = type(self).objects.filter(pk=self.pk).values_list("status", flat=True).first() if self.pk else None
            changed_fields = set()
            if previous != self.status:
                now = timezone.now()
                if previous == "CANCELED" and self.status in ("PENDING", "APPROVED", "WAITLIST"):
                    self.requested_at = now
                    self.decided_at = self.confirmed_at = self.cancelled_at = None
                    changed_fields.update(("requested_at", "decided_at", "confirmed_at", "cancelled_at"))
                if self.status != "WAITLIST" or previous == "CANCELED":
                    self.seat_offered_at = None
                    changed_fields.add("seat_offered_at")
                if self.status in ("APPROVED", "REJECTED"):
                    self.decided_at = now
                    changed_fields.add("decided_at")
                if self.status == "APPROVED":
                    self.confirmed_at = now
                    changed_fields.add("confirmed_at")
                if self.status == "CANCELED":
                    self.cancelled_at = now
                    changed_fields.add("cancelled_at")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | changed_fields
        super().save(*args, **kwargs)

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
        Registration, on_delete=models.CASCADE, related_name="payment", verbose_name="Inscrição"
    )
    amount = models.DecimalField("Valor Pago", max_digits=10, decimal_places=2)
    status = models.CharField("Status", max_length=50)
    method = models.CharField("Método de Pagamento", max_length=50)
    paid_at = models.DateTimeField("Pago em", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"

    def __str__(self):
        return f"Pagamento: {self.registration}"


class Attendance(models.Model):
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name="attendance", verbose_name="Inscrição"
    )
    attended = models.BooleanField("Presente", default=False)
    check_in_at = models.DateTimeField("Entrada registrada em", blank=True, null=True)
    notes = models.TextField("Observações", blank=True, null=True)

    class Meta:
        verbose_name = "Presença"
        verbose_name_plural = "Presenças"

    def __str__(self):
        return f"Presença: {self.registration}"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", verbose_name="Destinatário")
    registration = models.ForeignKey(Registration, on_delete=models.SET_NULL, null=True, related_name="notifications", verbose_name="Inscrição")
    message = models.TextField("Mensagem")
    created_at = models.DateTimeField("Criada em", auto_now_add=True)
    read_at = models.DateTimeField("Lida em", null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
