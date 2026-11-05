from django.contrib import admin
from config.admin_widgets import ClockAdminMixin
from registrations.models import Registration 
from .models import Activity, Location, Modality


class PriceFilter(admin.SimpleListFilter):
    title = "Valor"
    parameter_name = "price_type"

    def lookups(self, request, model_admin):
        return (
            ("free", "Gratuito"),
            ("paid", "Pago"),
        )

    def queryset(self, request, queryset):
        if self.value() == "free":
            return queryset.filter(price=0)
        if self.value() == "paid":
            return queryset.filter(price__gt=0)
        return queryset


class RegistrationInline(ClockAdminMixin, admin.TabularInline):
    model = Registration
    extra = 0
    show_change_link = True
    fields = [
        "participant",
        "status",
        "requested_at",
        "decided_at",
        "confirmed_at",
        "organizer_notes",
    ]
    readonly_fields = ["requested_at"]


@admin.register(Modality)
class ModalityAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    search_fields = ["name"]
    list_filter = ["is_active"]
    fieldsets = (
        ("Informações da Modalidade", {"fields": ("name", "description", "is_active")}),
    )

    # Restringe edição/deleção de cadastros base apenas para o superusuário
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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

    # Restringe edição/deleção de cadastros base apenas para o superusuário
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Activity)
class ActivityAdmin(ClockAdminMixin, admin.ModelAdmin):
    list_display = [
        "title",
        "organizer",
        "modality",
        "location",
        "starts_at",
        "status",
        "max_participants",
        "price",
    ]
    list_filter = [
        "status",
        "registration_type",
        "modality",
        "organizer",
        "location__city",
        PriceFilter,
        "starts_at",
    ]
    search_fields = ["title", "description", "organizer__username"]
    list_select_related = ["organizer", "modality", "location"]
    date_hierarchy = "starts_at"
    inlines = [RegistrationInline]
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

    def save_model(self, request, obj, form, change):
        if getattr(obj, "organizer", None) is None:
            obj.organizer = request.user
        obj.save()

    # Filtra listagem: Admin vê tudo; organizador vê as dele; participante vê as que está inscrito
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.has_organizer_group():
            return qs.filter(organizer=request.user)
        return qs.none()

    # Controle de visibilidade do formulário de edição
    def has_view_permission(self, request, obj=None):
        if not super().has_view_permission(request, obj):
            return False
        if obj is None or request.user.is_superuser:
            return True
        if obj.organizer_id == request.user.pk:
            return True
        return obj.registrations.filter(participant=request.user).exists()

    # Controle de edição: Apenas o dono ou o Admin podem alterar
    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if obj is None or request.user.is_superuser:
            return True
        return obj.organizer_id == request.user.pk

    # Controle de exclusão: Apenas o dono ou o Admin podem apagar
    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if obj is None or request.user.is_superuser:
            return True
        return obj.organizer_id == request.user.pk
