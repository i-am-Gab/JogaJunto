from django.contrib import admin
from config.admin_widgets import ClockAdminMixin

from .models import Attendance, Payment, Registration


class OrganizerScopedAdminMixin(ClockAdminMixin):
    organizer_lookup = None
    participant_lookup = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if not request.user.has_organizer_group():
            return qs.none()
        return qs.filter(**{self.organizer_lookup: request.user}).distinct()

    def _allowed(self, request, obj):
        if request.user.is_superuser:
            return True
        if not request.user.has_organizer_group():
            return False
        return obj is None or self.get_queryset(request).filter(pk=obj.pk).exists()

    def has_view_permission(self, request, obj=None):
        return self._allowed(request, obj) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return self._allowed(request, None) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._allowed(request, obj) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._allowed(request, obj) and super().has_delete_permission(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "activity":
                kwargs["queryset"] = db_field.remote_field.model.objects.filter(organizer=request.user)
            elif db_field.name == "registration":
                kwargs["queryset"] = Registration.objects.filter(activity__organizer=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



@admin.register(Registration)
class RegistrationAdmin(OrganizerScopedAdminMixin, admin.ModelAdmin):
    readonly_fields = ["requested_at", "decided_at", "confirmed_at", "cancelled_at", "seat_offered_at"]
    organizer_lookup = "activity__organizer"
    participant_lookup = "participant"
    list_display = ["participant", "activity", "status", "requested_at"]
    list_filter = ["status", "requested_at", "activity__status", "activity__modality"]
    search_fields = ["participant__username", "activity__title"]
    list_select_related = ["participant", "activity", "activity__organizer"]
    date_hierarchy = "requested_at"
    autocomplete_fields = ["activity"]

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if obj is None or request.user.is_superuser:
            return True
        return obj.activity.organizer_id == request.user.pk

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if obj is None or request.user.is_superuser:
            return True
        return obj.activity.organizer_id == request.user.pk


@admin.register(Payment)
class PaymentAdmin(OrganizerScopedAdminMixin, admin.ModelAdmin):
    organizer_lookup = "registration__activity__organizer"
    participant_lookup = "registration__participant"
    list_display = ["registration", "amount", "status", "method", "paid_at"]
    list_filter = ["status", "method"]
    search_fields = [
        "registration__participant__username",
        "registration__activity__title",
    ]
    list_select_related = [
        "registration",
        "registration__activity",
        "registration__participant",
    ]
    date_hierarchy = "created_at"


@admin.register(Attendance)
class AttendanceAdmin(OrganizerScopedAdminMixin, admin.ModelAdmin):
    organizer_lookup = "registration__activity__organizer"
    participant_lookup = "registration__participant"
    list_display = ["registration", "attended", "check_in_at"]
    list_filter = ["attended"]
    search_fields = [
        "registration__participant__username",
        "registration__activity__title",
    ]
    list_select_related = [
        "registration",
        "registration__activity",
        "registration__participant",
    ]
    date_hierarchy = "check_in_at"
