from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


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

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
