from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from activities.views import home, subscribe_activity, create_activity

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Rotas nativas de autenticação do Django (Login e Logout para o Front-end)
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    
    # Habilita outras rotas de contas caso necessário no futuro (troca de senha, etc)
    path("contas/", include("django.contrib.auth.urls")),
    
    # Rotas da Aplicação
    path("", home, name="home"),
    path("atividade/nova/", create_activity, name="create_activity"),
    path("atividade/<int:activity_id>/inscrever/", subscribe_activity, name="subscribe_activity"),
]