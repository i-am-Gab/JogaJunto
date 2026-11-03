from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import GROUP_ORGANIZER, User
from .permissions import sync_user_group


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Informações Adicionais", {"fields": ("phone", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Perfil de acesso", {"fields": ("phone", "role")}),
    )
    list_display = [
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
        "role",
        "is_staff",
    ]
    list_filter = ["role", "is_staff", "is_superuser", "groups", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.groups.filter(name=GROUP_ORGANIZER).exists():
            return qs
        return qs.filter(pk=request.user.pk)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if request.user.is_superuser or obj is None:
            return True
        if request.user.groups.filter(name=GROUP_ORGANIZER).exists():
            return obj.pk == request.user.pk
        return obj.pk == request.user.pk

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.is_superuser:
            sync_user_group(obj)
