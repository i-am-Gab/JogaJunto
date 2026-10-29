from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Activity
from registrations.models import Registration
from .forms import ActivityForm


def home(request):
    # Conta inscrições que NÃO foram canceladas nem rejeitadas
    activities = (
        Activity.objects.filter(status="PUBLISHED")
        .select_related("modality", "location")
        .annotate(
            active_registrations=Count(
                "registrations",
                filter=~Q(registrations__status__in=["REJECTED", "CANCELED"]),
            )
        )
        .order_by("starts_at")
    )

    user_registrations = []
    if request.user.is_authenticated:
        user_registrations = Registration.objects.filter(
            participant=request.user
        ).values_list("activity_id", flat=True)

    return render(
        request,
        "home.html",
        {"activities": activities, "user_registrations": user_registrations},
    )


@login_required(login_url="/admin/login/")
def create_activity(request):
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


@login_required(login_url="/admin/login/")
def subscribe_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id, status="PUBLISHED")

    if activity.organizer == request.user:
        messages.warning(request, "Você é o organizador desta atividade!")
        return redirect("home")

    current_subscriptions = (
        Registration.objects.filter(activity=activity)
        .exclude(status__in=["REJECTED", "CANCELED"])
        .count()
    )
    if current_subscriptions >= activity.max_participants:
        messages.error(
            request, "Esta atividade já atingiu o limite máximo de participantes."
        )
        return redirect("home")

    try:
        initial_status = (
            "APPROVED" if activity.registration_type == "AUTO" else "PENDING"
        )
        Registration.objects.create(
            activity=activity, participant=request.user, status=initial_status
        )
        messages.success(
            request, f"Inscrição realizada com sucesso em {activity.title}!"
        )
    except Exception as e:
        messages.error(request, "Você já possui uma inscrição para esta atividade.")

    return redirect("home")
