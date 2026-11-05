from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_POST

from django.core.exceptions import PermissionDenied
from registrations.models import Registration
from registrations.waitlist import occupied_seats, offer_available_seats

from .forms import ActivityForm
from .models import Activity


def home(request):
    # Conta inscrições que NÃO foram canceladas nem rejeitadas
    activities = (
        Activity.objects.filter(status="PUBLISHED")
        .select_related("modality", "location", "organizer")
        .annotate(
            active_registrations=Count(
                "registrations",
                filter=Q(registrations__status__in=["PENDING", "APPROVED"]) | Q(registrations__status="WAITLIST", registrations__seat_offered_at__isnull=False),
            )
        )
        .order_by("starts_at")
    )

    registrations = {}
    if request.user.is_authenticated:
        registrations = {row.activity_id: row for row in Registration.objects.filter(participant=request.user).select_related("activity")}
    for activity in activities:
        registration = registrations.get(activity.pk)
        activity.user_registration_status = registration.status if registration else None
        activity.user_seat_offered = registration.can_confirm_seat if registration else False
    return render(request, "home.html", {"activities": activities})



@login_required
def create_activity(request):
    if not request.user.has_organizer_group():
        raise PermissionDenied
    if request.method == "POST":
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.organizer = request.user
            activity.status = "PUBLISHED"  # Publica direto para facilitar o fluxo
            activity.save()
            messages.success(request, "Atividade criada com sucesso!")
            return redirect("home")
    else:
        form = ActivityForm()

    return render(request, "activity_form.html", {"form": form})


@login_required
@require_POST
def subscribe_activity(request, activity_id):
    destination = "my_registrations" if request.POST.get("source") == "mine" else "home"
    try:
        with transaction.atomic():
            activity = get_object_or_404(Activity.objects.select_for_update(), pk=activity_id)
            if activity.organizer == request.user:
                messages.warning(request, "Você é o organizador desta atividade!")
                return redirect(destination)
            registration = Registration.objects.select_for_update().filter(activity=activity, participant=request.user).first()
            if registration and registration.status != "CANCELED":
                messages.warning(request, "Você já possui uma inscrição para esta atividade. Apenas inscrições canceladas podem ser refeitas.")
                return redirect(destination)
            if not activity.accepts_registrations:
                messages.warning(request, "Esta atividade não aceita inscrições: o prazo terminou, ela já começou ou não está publicada.")
                return redirect(destination)
            offer_available_seats(activity.pk)
            occupied = occupied_seats(activity.registrations).count()
            initial_status = "APPROVED" if activity.registration_type == "AUTO" else "PENDING"
            if occupied >= activity.max_participants:
                initial_status = "WAITLIST"
            if registration:
                registration.status = initial_status
                registration.save(update_fields=["status"])
            else:
                Registration.objects.create(activity=activity, participant=request.user, status=initial_status)
        if initial_status == "WAITLIST":
            messages.info(request, "A atividade está lotada. Você entrou na lista de espera e será avisado quando uma vaga estiver disponível.")
        elif initial_status == "PENDING":
            messages.info(request, f"Inscrição em {activity.title} pendente de aprovação do organizador.")
        else:
            messages.success(request, f"Inscrição confirmada em {activity.title}!")
    except IntegrityError:
        messages.warning(request, "A inscrição já foi registrada. Atualize a página para acompanhar a situação.")
    return redirect(destination)
