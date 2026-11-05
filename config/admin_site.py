from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class RoleAdminSite(AdminSite):
    def has_permission(self, request):
        return super().has_permission(request) and request.user.has_organizer_group()


class RoleAdminConfig(AdminConfig):
    default_site = "config.admin_site.RoleAdminSite"
