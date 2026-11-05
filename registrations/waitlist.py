from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from activities.models import Activity
from .models import Notification, Registration


def occupied_seats(queryset):
    return queryset.filter(
        Q(status__in=("PENDING", "APPROVED")) |
        Q(status="WAITLIST", seat_offered_at__isnull=False)
    )


@transaction.atomic
def offer_available_seats(activity_id):
    """Reserva as vagas por ordem da fila; o participante ainda precisa confirmar."""
    activity = Activity.objects.select_for_update().get(pk=activity_id)
    if not activity.accepts_registrations:
        return
    available = max(0, activity.max_participants - occupied_seats(activity.registrations).count())
    queue = activity.registrations.select_for_update().filter(
        status="WAITLIST", seat_offered_at__isnull=True,
    ).order_by("requested_at", "pk")[:available]
    deadline = timezone.localtime(activity.confirmation_deadline).strftime("%d/%m/%Y às %H:%M")
    for registration in queue:
        registration.seat_offered_at = timezone.now()
        registration.save(update_fields=["seat_offered_at"])
        Notification.objects.create(
            recipient=registration.participant, registration=registration,
            message=f'Uma vaga em "{activity.title}" foi liberada e está reservada para você. Confirme em Minhas inscrições até {deadline}.',
        )
