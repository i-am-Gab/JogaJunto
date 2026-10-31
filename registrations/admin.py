from django.contrib import admin
from django.db.models import Q

from .models import Attendance, Payment, Registration


class OrganizerScopedAdminMixin:
    organizer_lookup = None
    participant_lookup = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        filters = Q()
        if self.organizer_lookup:
            filters |= Q(**{self.organizer_lookup: request.user})
        if self.participant_lookup:
            filters |= Q(**{self.participant_lookup: request.user})
        return qs.filter(filters).distinct()


@admin.register(Registration)
class RegistrationAdmin(OrganizerScopedAdminMixin, admin.ModelAdmin):
    organizer_lookup = "activity__organizer"
    participant_lookup = "participant"
    list_display = ["participant", "activity", "status", "requested_at"]
    list_filter = ["status", "requested_at", "activity__status", "activity__modality"]
    search_fields = ["participant__username", "activity__title"]
    list_select_related = ["participant", "activity", "activity__organizer"]
    date_hierarchy = "requested_at"
    autocomplete_fields = ["participant", "activity"]

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
