from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from activities.views import home, subscribe_activity, create_activity
from accounts.views import signup
from registrations import views as registration_views
from accounts.forms import LoginForm

urlpatterns = [
    path("minhas-inscricoes/<int:registration_id>/confirmar-vaga/", registration_views.confirm_waitlist_seat, name="confirm_waitlist_seat"),
    path("minhas-inscricoes/", registration_views.my_registrations, name="my_registrations"),
    path("minhas-inscricoes/<int:registration_id>/cancelar/", registration_views.cancel_registration, name="cancel_registration"),
    path("organizador/inscricoes/", registration_views.review_registrations, name="review_registrations"),
    path("organizador/inscricoes/<int:registration_id>/decidir/", registration_views.decide_registration, name="decide_registration"),
    path("notificacoes/", registration_views.notifications, name="notifications"),
    path("notificacoes/ler-todas/", registration_views.read_all_notifications, name="read_all_notifications"),
    path("notificacoes/<int:notification_id>/ler/", registration_views.read_notification, name="read_notification"),
    path("cadastro/", signup, name="signup"),
    path("admin/", admin.site.urls),
    
    # Rotas nativas de autenticação do Django (Login e Logout para o Front-end)
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", authentication_form=LoginForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    
    # Habilita outras rotas de contas caso necessário no futuro (troca de senha, etc)
    path("contas/", include(("django.contrib.auth.urls", "auth"), namespace="auth")),
    
    # Rotas da Aplicação
    path("", home, name="home"),
    path("atividade/nova/", create_activity, name="create_activity"),
    path("atividade/<int:activity_id>/inscrever/", subscribe_activity, name="subscribe_activity"),
]
