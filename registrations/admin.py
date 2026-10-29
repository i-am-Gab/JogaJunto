from django.contrib import admin
from .models import Registration, Payment, Attendance


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ["participant", "activity", "status", "requested_at"]
    list_filter = ["status", "requested_at"]
    search_fields = ["participant__username", "activity__title"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["registration", "amount", "status", "method", "paid_at"]
    list_filter = ["status", "method"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["registration", "attended", "check_in_at"]
    list_filter = ["attended"]
