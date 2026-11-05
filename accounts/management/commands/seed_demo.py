from collections import Counter
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import User, ROLE_ORGANIZER, ROLE_PARTICIPANT
from accounts.permissions import ORGANIZER_PERMISSIONS
from activities.models import Activity, Location, Modality
from registrations.models import Notification, Registration


DEMO_PASSWORD = "JogaJuntoDemo!2026"
DEMO_USERS = (
    ("demo_admin", "Admin", ROLE_PARTICIPANT, True),
    ("demo_organizador", "Rafael", ROLE_ORGANIZER, False),
    ("demo_organizador2", "Mariana", ROLE_ORGANIZER, False),
    ("demo_ana", "Ana", ROLE_PARTICIPANT, False),
    ("demo_bruno", "Bruno", ROLE_PARTICIPANT, False),
    ("demo_carla", "Carla", ROLE_PARTICIPANT, False),
    ("demo_diego", "Diego", ROLE_PARTICIPANT, False),
)


class Command(BaseCommand):
    help = "Cria exemplos de demonstração, sem sobrescrever dados existentes."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument("--password", default=DEMO_PASSWORD, help="Senha apenas das contas criadas nesta execução.")

    def create_if_missing(self, model, lookup, defaults, category):
        # Há modelos sem chave natural única. Escolher o primeiro também preserva
        # bases antigas que já contenham mais de um registro com o mesmo nome.
        existing = model.objects.filter(**lookup).order_by("pk").first()
        if existing:
            self.preserved[category] += 1
            return existing, False
        obj = model(**lookup, **defaults)
        obj.full_clean()
        # Não dispara os sinais que sincronizam grupos ou redistribuem vagas.
        # Datas e notificações dos novos exemplos são configuradas explicitamente.
        model.objects.bulk_create([obj])
        self.created[category] += 1
        return obj, True

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["password"]:
            raise CommandError("Informe uma senha não vazia para as contas de demonstração.")
        self.created, self.preserved = Counter(), Counter()
        self.now = timezone.now()

        # Não usa nem modifica uma conta homônima que não pertença aos exemplos.
        for username, _, _, _ in DEMO_USERS:
            user = User.objects.filter(username=username).first()
            if user and user.email != f"{username}@demo.jogajunto.invalid":
                raise CommandError(f'A conta "{username}" já existe e não é uma conta de demonstração. Nenhum dado foi alterado.')

        users = {}
        permission_filter = Q(pk__in=[])
        for app_label, codename in ORGANIZER_PERMISSIONS:
            permission_filter |= Q(content_type__app_label=app_label, codename=codename)
        permissions = list(Permission.objects.filter(permission_filter))
        for username, name, role, superuser in DEMO_USERS:
            existing = User.objects.filter(username=username).first()
            if existing:
                self.preserved["usuários"] += 1
                users[username] = existing
                continue
            candidate = User(username=username, email=f"{username}@demo.jogajunto.invalid", first_name=name,
                             last_name="Demonstração", role=role, is_staff=superuser or role == ROLE_ORGANIZER,
                             is_superuser=superuser, is_active=True)
            candidate.set_password(options["password"])
            user, created = self.create_if_missing(User, {"username": username}, {
                field.attname: getattr(candidate, field.attname)
                for field in User._meta.concrete_fields if not field.primary_key and field.name != "username"
            }, "usuários")
            if created and role == ROLE_ORGANIZER:
                # Permissões só da conta nova; não altera os grupos compartilhados.
                user.user_permissions.add(*permissions)
            users[username] = user

        modalities = {}
        for name in ("Corrida", "Futebol", "Ciclismo", "Caminhada"):
            modalities[name], _ = self.create_if_missing(Modality, {"name": f"[DEMO] {name}"}, {
                "description": "Modalidade de demonstração do JogaJunto.", "is_active": True,
            }, "modalidades")
        locations = []
        for index, name in enumerate(("Parque Central", "Quadra do Bairro", "Praça dos Esportes"), 1):
            location, _ = self.create_if_missing(Location, {"name": f"[DEMO] {name}"}, {
                "street": "Rua de Demonstração", "number": str(index * 100), "neighborhood": "Centro",
                "city": "Lavras", "state": "MG", "zip_code": "37200-000",
                "reference_point": "Local fictício para testes.",
            }, "locais")
            locations.append(location)

        # Inscrições: participante, situação, vaga reservada.
        scenarios = (
            ("Corrida com aprovação", "Corrida", 0, "demo_organizador", "MANUAL", "PUBLISHED", 10,
             (("ana", "PENDING", False), ("bruno", "APPROVED", False), ("carla", "REJECTED", False), ("diego", "CANCELED", False))),
            ("Futebol com lista de espera", "Futebol", 1, "demo_organizador", "AUTO", "PUBLISHED", 1,
             (("ana", "APPROVED", False), ("bruno", "WAITLIST", False), ("carla", "WAITLIST", False))),
            ("Caminhada com vaga reservada", "Caminhada", 2, "demo_organizador2", "AUTO", "PUBLISHED", 1,
             (("ana", "CANCELED", False), ("diego", "WAITLIST", True))),
            ("Pedal aberto", "Ciclismo", 0, "demo_organizador2", "AUTO", "PUBLISHED", 8,
             (("ana", "APPROVED", False), ("bruno", "APPROVED", False))),
            ("Atividade em rascunho", "Futebol", 1, "demo_organizador", "MANUAL", "DRAFT", 12, ()),
            ("Atividade cancelada", "Corrida", 0, "demo_organizador2", "AUTO", "CANCELED", 10,
             (("bruno", "CANCELED", False),)),
            ("Caminhada concluída", "Caminhada", 2, "demo_organizador2", "AUTO", "FINISHED", 10,
             (("ana", "APPROVED", False),)),
        )
        for index, (title, modality, location, organizer, kind, status, capacity, registrations) in enumerate(scenarios):
            starts_at = timezone.localtime(self.now).replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=7 + 2 * index)
            if status == "FINISHED":
                starts_at = starts_at - timedelta(days=30)
            activity, created = self.create_if_missing(Activity, {
                "title": f"[DEMO] {title}", "organizer": users[organizer],
            }, {
                "description": "Atividade fictícia para explorar os fluxos do JogaJunto.",
                "modality": modalities[modality], "location": locations[location], "registration_type": kind,
                "status": status, "max_participants": capacity, "price": 0,
                "starts_at": starts_at, "ends_at": starts_at + timedelta(hours=2),
                "confirmation_deadline": starts_at - timedelta(days=1),
            }, "atividades")
            if not created:
                # Não repõe inscrições, redefine situações ou datas de uma atividade existente.
                continue
            for order, (participant, registration_status, offered) in enumerate(registrations):
                self.create_registration(activity, users[f"demo_{participant}"], registration_status, offered, order)

        for category in ("usuários", "modalidades", "locais", "atividades", "inscrições", "notificações"):
            self.stdout.write(f"{category}: {self.created[category]} criado(s); {self.preserved[category]} preservado(s).")
        self.stdout.write(self.style.SUCCESS("Demonstração pronta. Registros existentes, senhas e permissões foram preservados."))
        self.stdout.write("Contas: " + ", ".join(user[0] for user in DEMO_USERS))
        self.stdout.write("As contas novas usam a senha documentada ou a informada em --password. Contas existentes mantêm a senha anterior.")

    def create_registration(self, activity, participant, status, offered, order):
        requested_at = min(self.now - timedelta(days=2), activity.starts_at - timedelta(days=2)) + timedelta(minutes=order)
        decided_at = requested_at + timedelta(hours=1) if status in ("APPROVED", "REJECTED") else None
        registration, created = self.create_if_missing(Registration, {"activity": activity, "participant": participant}, {
            "status": status, "decided_at": decided_at,
            "confirmed_at": decided_at if status == "APPROVED" else None,
            "cancelled_at": requested_at + timedelta(hours=2) if status == "CANCELED" else None,
            "seat_offered_at": self.now if offered else None,
            "organizer_notes": "Observação interna de demonstração.",
        }, "inscrições")
        if not created:
            return
        # auto_now_add é aplicado no INSERT; ajusta apenas a linha recém-criada.
        registration.requested_at = requested_at
        Registration.objects.bulk_update([registration], ["requested_at"])
        message = f'Situação de demonstração em "{activity.title}": {registration.get_status_display()}.'
        if offered:
            deadline = timezone.localtime(activity.confirmation_deadline).strftime("%d/%m/%Y às %H:%M")
            message = f'Uma vaga em "{activity.title}" está reservada para você. Confirme em Minhas inscrições até {deadline}.'
        Notification.objects.create(recipient=participant, registration=registration, message=message)
        self.created["notificações"] += 1
        if status == "PENDING":
            Notification.objects.create(recipient=activity.organizer, registration=registration,
                                        message=f'{participant} aguarda sua aprovação em "{activity.title}".')
            self.created["notificações"] += 1
