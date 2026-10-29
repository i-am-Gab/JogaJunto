from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Informações Adicionais", {"fields": ("phone", "role")}),
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
