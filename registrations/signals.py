from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Notification, Registration


@receiver(pre_save, sender=Registration)
def remember_status(sender, instance, raw=False, **kwargs):
    if not raw:
        instance._previous_status = sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()


@receiver(post_save, sender=Registration)
def notify_registration(sender, instance, created, raw=False, update_fields=None, **kwargs):
    if raw or (update_fields is not None and "status" not in update_fields):
        return
    if not created and getattr(instance, "_previous_status", None) == instance.status:
        return
    descriptions = {
        "PENDING": "está pendente de aprovação do organizador",
        "APPROVED": "foi aprovada e sua vaga está confirmada",
        "REJECTED": "foi rejeitada pelo organizador",
        "WAITLIST": "está na lista de espera",
        "CANCELED": "foi cancelada",
    }
    Notification.objects.create(
        recipient=instance.participant, registration=instance,
        message=f'Sua inscrição em "{instance.activity.title}" {descriptions[instance.status]}.',
    )
    if instance.status == "PENDING" and (created or getattr(instance, "_previous_status", None) in ("CANCELED", "WAITLIST")):
        Notification.objects.create(
            recipient=instance.activity.organizer, registration=instance,
            message=f'{instance.participant} solicitou inscrição em "{instance.activity.title}". Aguardando sua aprovação.',
        )
    if instance.status == "CANCELED":
        Notification.objects.create(
            recipient=instance.activity.organizer, registration=instance,
            message=f'A inscrição de {instance.participant} em "{instance.activity.title}" foi cancelada.',
        )
    if instance.status in ("CANCELED", "REJECTED"):
        from .waitlist import offer_available_seats
        offer_available_seats(instance.activity_id)
