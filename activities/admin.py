from django.contrib import admin
from django.db import models
from .models import Modality, Location, Activity


@admin.register(Modality)
class ModalityAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    search_fields = ["name"]
    list_filter = ["is_active"]
    # Tradução do formulário caso o Jazzmin não traduza automaticamente
    fieldsets = (
        ("Informações da Modalidade", {"fields": ("name", "description", "is_active")}),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "neighborhood", "city", "state"]
    search_fields = ["name", "city", "neighborhood"]
    list_filter = ["state", "city"]
    fieldsets = (
        ("Informações Principais", {"fields": ("name", "reference_point")}),
        (
            "Endereço",
            {
                "fields": (
                    "street",
                    "number",
                    "neighborhood",
                    "city",
                    "state",
                    "zip_code",
                    "complement",
                )
            },
        ),
        (
            "Geolocalização (Mapa no Futuro)",
            {
                "fields": ("latitude", "longitude"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "organizer",
        "modality",
        "starts_at",
        "status",
        "max_participants",
        "price",
    ]
    list_filter = ["status", "registration_type", "modality", "starts_at"]
    search_fields = ["title", "description", "organizer__username"]
    date_hierarchy = "starts_at"

    # Ocultar o organizador do formulário para o preenchimento automático
    exclude = ["organizer"]

    fieldsets = (
        (
            "Detalhes da Atividade",
            {"fields": ("title", "description", "modality", "location")},
        ),
        (
            "Configurações de Horário e Vagas",
            {"fields": ("starts_at", "ends_at", "max_participants")},
        ),
        (
            "Financeiro e Confirmação",
            {
                "fields": (
                    "price",
                    "confirmation_deadline",
                    "registration_type",
                    "status",
                )
            },
        ),
    )

    # Preenche o organizador automaticamente com o usuário logado
    def save_model(self, request, obj, form, change):
        if getattr(obj, "organizer", None) is None:
            obj.organizer = request.user
        obj.save()

    # Filtra a visualização (Organizador vê as próprias atividades, Administrador vê tudo)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organizer=request.user)
