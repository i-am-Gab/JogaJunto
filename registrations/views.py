from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from activities.models import Activity
from .models import Registration
from django.http import Http404, HttpResponseBadRequest
from .waitlist import occupied_seats


@login_required
@require_POST
def confirm_waitlist_seat(request, registration_id):
    queryset = Registration.objects.filter(participant=request.user)
    registration = get_object_or_404(queryset, pk=registration_id)
    with transaction.atomic():
        activity = Activity.objects.select_for_update().get(pk=registration.activity_id)
        registration = queryset.select_for_update().get(pk=registration.pk)
        registration.activity = activity
        if not registration.can_confirm_seat:
            messages.warning(request, "Não há uma vaga reservada para confirmar ou o prazo de inscrição terminou.")
        elif occupied_seats(activity.registrations.exclude(pk=registration.pk)).count() >= activity.max_participants:
            messages.warning(request, "Não há vagas disponíveis. Entre em contato com o organizador.")
        else:
            registration.status = "APPROVED" if activity.registration_type == "AUTO" else "PENDING"
            registration.save(update_fields=["status"])
            if registration.status == "PENDING":
                messages.success(request, "Você aceitou a vaga. Sua inscrição aguarda aprovação do organizador.")
            else:
                messages.success(request, "Vaga aceita! Sua inscrição está confirmada.")
    return redirect("my_registrations")


@login_required
def my_registrations(request):
    queryset = Registration.objects.filter(participant=request.user).select_related("activity__location", "activity__modality", "activity__organizer")
    selected = request.GET.get("situacao", "ALL")
    if selected not in {"ALL", *dict(Registration.STATUS_CHOICES)}:
        selected = "ALL"
    counts = dict(queryset.values("status").annotate(total=Count("pk")).values_list("status", "total"))
    labels = [("ALL", "Todas"), ("PENDING", "Pendentes"), ("APPROVED", "Confirmadas"), ("WAITLIST", "Lista de espera"), ("REJECTED", "Rejeitadas"), ("CANCELED", "Canceladas")]
    tabs = [{"value": value, "label": label, "count": sum(counts.values()) if value == "ALL" else counts.get(value, 0)} for value, label in labels]
    if selected != "ALL":
        queryset = queryset.filter(status=selected)
    page = Paginator(queryset.order_by("-requested_at", "-pk"), 15).get_page(request.GET.get("page"))
    return render(request, "registrations/mine.html", {"page_obj": page, "tabs": tabs, "selected": selected})


@login_required
@require_POST
def cancel_registration(request, registration_id):
    queryset = Registration.objects.filter(participant=request.user)
    registration = get_object_or_404(queryset, pk=registration_id)
    with transaction.atomic():
        # Mesma ordem de bloqueio da aprovação, para não cancelar e aprovar ao mesmo tempo.
        activity = Activity.objects.select_for_update().get(pk=registration.activity_id)
        registration = queryset.select_for_update().get(pk=registration.pk)
        registration.activity = activity
        if registration.status == "CANCELED":
            messages.info(request, "Esta inscrição já está cancelada.")
        elif not registration.can_cancel:
            messages.warning(request, "Esta inscrição não pode mais ser cancelada. O cancelamento está disponível para inscrições ativas antes do início da atividade.")
        else:
            registration.status = "CANCELED"
            registration.save(update_fields=["status"])
            messages.success(request, f'Sua inscrição em "{activity.title}" foi cancelada. O organizador foi notificado.')
    return redirect("my_registrations")


@login_required
def notifications(request):
    page = Paginator(request.user.notifications.select_related("registration__activity"), 20).get_page(request.GET.get("page"))
    return render(request, "notifications.html", {"page_obj": page})


@login_required
@require_POST
def read_notification(request, notification_id):
    notification = get_object_or_404(request.user.notifications, pk=notification_id)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("notifications")


@login_required
@require_POST
def read_all_notifications(request):
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    return redirect("notifications")

def organizer_registrations(user):
    if not user.has_organizer_group():
        raise PermissionDenied
    queryset = Registration.objects.select_related("activity", "participant")
    return queryset if user.is_superuser else queryset.filter(activity__organizer=user)


@login_required
def review_registrations(request):
    queryset = organizer_registrations(request.user)
    activities = Activity.objects.all() if request.user.is_superuser else Activity.objects.filter(organizer=request.user)
    activity_id = request.GET.get("atividade", "")
    if activity_id:
        activity = get_object_or_404(activities, pk=activity_id) if activity_id.isdecimal() else None
        if activity is None:
            raise Http404
        queryset = queryset.filter(activity=activity)
    selected = request.GET.get("situacao", "PENDING")
    if selected not in {"ALL", *dict(Registration.STATUS_CHOICES)}:
        selected = "PENDING"
    counts = dict(queryset.values("status").annotate(total=Count("pk")).values_list("status", "total"))
    tabs = [("PENDING", "Pendentes"), ("APPROVED", "Aprovadas"), ("REJECTED", "Rejeitadas"), ("ALL", "Todas")]
    tabs = [{"value": value, "label": label, "count": sum(counts.values()) if value == "ALL" else counts.get(value, 0)} for value, label in tabs]
    if selected != "ALL":
        queryset = queryset.filter(status=selected)
    page = Paginator(queryset.order_by("requested_at", "pk"), 15).get_page(request.GET.get("page"))
    return render(request, "registrations/review.html", {
        "page_obj": page, "tabs": tabs, "selected": selected,
        "activities": activities.order_by("title"), "activity_id": activity_id,
    })


@login_required
@require_POST
def decide_registration(request, registration_id):
    queryset = organizer_registrations(request.user)
    registration = get_object_or_404(queryset, pk=registration_id)
    decision = request.POST.get("decision")
    if decision not in ("APPROVED", "REJECTED", "SAVE_NOTES"):
        return HttpResponseBadRequest("Escolha aprovar ou rejeitar a solicitação.")
    with transaction.atomic():
        activity = Activity.objects.select_for_update().get(pk=registration.activity_id)
        registration = queryset.select_for_update().get(pk=registration.pk)
        if decision == "SAVE_NOTES":
            registration.organizer_notes = request.POST.get("organizer_notes", "").strip()
            registration.save(update_fields=["organizer_notes"])
            messages.success(request, "Notas do organizador salvas.")
        elif registration.status != "PENDING":
            messages.warning(request, "Esta solicitação já foi analisada. Atualize a lista para ver a situação atual.")
        elif activity.status != "PUBLISHED":
            messages.warning(request, "Esta atividade não está publicada e não aceita decisões de inscrição.")
        elif decision == "APPROVED" and activity.registrations.filter(status="APPROVED").count() >= activity.max_participants:
            messages.error(request, "Não há vagas disponíveis. A solicitação permanece pendente.")
        else:
            registration.status = decision
            if "organizer_notes" in request.POST:
                registration.organizer_notes = request.POST["organizer_notes"].strip()
            registration.save(update_fields=["status", "organizer_notes"])
            label = "aprovada" if decision == "APPROVED" else "rejeitada"
            messages.success(request, f"Inscrição de {registration.participant} {label}. O participante foi notificado.")
    if request.POST.get("source") == "activity":
        from django.urls import reverse
        return redirect(reverse("admin:activities_activity_change", args=[activity.pk]) + "#inscri%C3%A7%C3%B5es-tab")
    from django.urls import reverse
    return redirect(reverse("review_registrations") + f"?situacao=ALL&atividade={registration.activity_id}#inscricao-{registration.pk}")
