from django.shortcuts import render
from .models import Activity


def home(request):
    # Consulta as atividades publicadas no banco de dados
    activities = (
        Activity.objects.filter(status="PUBLISHED")
        .select_related("modality", "location")
        .order_by("starts_at")
    )
    return render(request, "home.html", {"activities": activities})
