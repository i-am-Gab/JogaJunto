from django.contrib import admin
from django.urls import path, include
from activities.views import home, subscribe_activity, create_activity

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "contas/", include("django.contrib.auth.urls")
    ),  # Habilita a rota /contas/logout/
    path("", home, name="home"),
    path("atividade/nova/", create_activity, name="create_activity"),
    path(
        "atividade/<int:activity_id>/inscrever/",
        subscribe_activity,
        name="subscribe_activity",
    ),
]
