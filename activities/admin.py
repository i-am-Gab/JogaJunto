from django.contrib import admin
from .models import Modality, Location, Activity


@admin.register(Modality)
class ModalityAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active"]
    search_fields = ["name"]
    list_filter = ["is_active"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "neighborhood", "city", "state"]
    search_fields = ["name", "city", "neighborhood"]
    list_filter = ["state", "city"]


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
