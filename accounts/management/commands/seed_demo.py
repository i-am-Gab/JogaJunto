from collections import Counter
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import User, ROLE_ORGANIZER, ROLE_PARTICIPANT
from accounts.permissions import ORGANIZER_PERMISSIONS
from activities.models import Activity, Location, Modality
from registrations.models import Attendance, Notification, Payment, Registration

DEMO_PASSWORD = "JogaJuntoDemo!2026"
DEMO_USERS = (
    ("demo_admin", "Admin", ROLE_PARTICIPANT, True),
    ("demo_organizador", "Rafael", ROLE_ORGANIZER, False),
    ("demo_organizador2", "Mariana", ROLE_ORGANIZER, False),
    ("demo_organizador3", "Lucas", ROLE_ORGANIZER, False),
    ("demo_organizador4", "Camila", ROLE_ORGANIZER, False),
    ("demo_ana", "Ana", ROLE_PARTICIPANT, False),
    ("demo_bruno", "Bruno", ROLE_PARTICIPANT, False),
    ("demo_carla", "Carla", ROLE_PARTICIPANT, False),
    ("demo_diego", "Diego", ROLE_PARTICIPANT, False),
)


class Command(BaseCommand):
    help = "Cria exemplos de demonstração com locais reais em várias cidades."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEMO_PASSWORD,
            help="Senha apenas das contas criadas nesta execução.",
        )

    def create_if_missing(self, model, lookup, defaults, category):
        existing = model.objects.filter(**lookup).order_by("pk").first()
        if existing:
            self.preserved[category] += 1
            return existing, False
        obj = model(**lookup, **defaults)
        obj.full_clean()
        model.objects.bulk_create([obj])
        self.created[category] += 1
        return obj, True

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["password"]:
            raise CommandError(
                "Informe uma senha não vazia para as contas de demonstração."
            )
        self.created, self.preserved = Counter(), Counter()
        self.now = timezone.now()

        for username, _, _, _ in DEMO_USERS:
            user = User.objects.filter(username=username).first()
            if user and user.email != f"{username}@demo.jogajunto.invalid":
                raise CommandError(
                    f'A conta "{username}" já existe e não é uma conta de demonstração. Nenhum dado foi alterado.'
                )

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
            candidate = User(
                username=username,
                email=f"{username}@demo.jogajunto.invalid",
                first_name=name,
                last_name="Demonstração",
                role=role,
                is_staff=superuser or role == ROLE_ORGANIZER,
                is_superuser=superuser,
                is_active=True,
            )
            candidate.set_password(options["password"])
            user, created = self.create_if_missing(
                User,
                {"username": username},
                {
                    field.attname: getattr(candidate, field.attname)
                    for field in User._meta.concrete_fields
                    if not field.primary_key and field.name != "username"
                },
                "usuários",
            )
            if created and role == ROLE_ORGANIZER:
                user.user_permissions.add(*permissions)
            users[username] = user

        modalities = {}
        for name in (
            "Corrida",
            "Futebol",
            "Ciclismo",
            "Caminhada",
            "Beach Tennis",
            "Vôlei",
        ):
            modalities[name], _ = self.create_if_missing(
                Modality,
                {"name": f"[DEMO] {name}"},
                {
                    "description": f"Prática coletiva de {name.lower()} na região.",
                    "is_active": True,
                },
                "modalidades",
            )

        real_locations = (
            {
                "name": "[DEMO] Campo da UFLA",
                "street": "Avenida Central",
                "number": "S/N",
                "neighborhood": "Inácio Valentim",
                "city": "Lavras",
                "state": "MG",
                "zip_code": "37200-000",
                "reference_point": "Complexo Esportivo da UFLA.",
                "latitude": Decimal("-21.231358"),
                "longitude": Decimal("-44.991580"),
            },
            {
                "name": "[DEMO] Praça Dr. Augusto Silva",
                "street": "Praça Doutor Augusto Silva",
                "number": "172",
                "neighborhood": "Centro",
                "city": "Lavras",
                "state": "MG",
                "zip_code": "37200-000",
                "reference_point": "Coreto central da praça.",
                "latitude": Decimal("-21.245420"),
                "longitude": Decimal("-45.000560"),
            },
            {
                "name": "[DEMO] Parque Ecológico Quaresmeiras",
                "street": "Rua Doutor Álvaro Botelho",
                "number": "500",
                "neighborhood": "Jardim Glória",
                "city": "Lavras",
                "state": "MG",
                "zip_code": "37200-000",
                "reference_point": "Portaria principal do parque.",
                "latitude": Decimal("-21.238900"),
                "longitude": Decimal("-44.996400"),
            },
            {
                "name": "[DEMO] Sunset Arena Lavras",
                "street": "Rua Comandante Soares Júnior",
                "number": "268",
                "neighborhood": "Arthur Bernardes",
                "city": "Lavras",
                "state": "MG",
                "zip_code": "37200-000",
                "reference_point": "Quadras de areia no centro de Lavras.",
                "latitude": Decimal("-21.248100"),
                "longitude": Decimal("-45.002800"),
            },
            {
                "name": "[DEMO] Clube de Nepomuceno",
                "street": "Rua Doutor Ernane Vilela Lima",
                "number": "202",
                "neighborhood": "Centro",
                "city": "Nepomuceno",
                "state": "MG",
                "zip_code": "37250-000",
                "reference_point": "Entrada das quadras poliesportivas.",
                "latitude": Decimal("-21.235800"),
                "longitude": Decimal("-45.235500"),
            },
            {
                "name": "[DEMO] Praça Padre José",
                "street": "Praça Padre José",
                "number": "180",
                "neighborhood": "Centro",
                "city": "Nepomuceno",
                "state": "MG",
                "zip_code": "37250-000",
                "reference_point": "Em frente à matriz em Nepomuceno.",
                "latitude": Decimal("-21.234500"),
                "longitude": Decimal("-45.236200"),
            },
            {
                "name": "[DEMO] Parque Novo Horizonte",
                "street": "Avenida dos Imigrantes",
                "number": "1000",
                "neighborhood": "Vargem",
                "city": "Varginha",
                "state": "MG",
                "zip_code": "37022-560",
                "reference_point": "Pista de caminhada e ciclismo.",
                "latitude": Decimal("-21.565800"),
                "longitude": Decimal("-45.437500"),
            },
            {
                "name": "[DEMO] Praça Apolônio Pereira",
                "street": "Praça Apolônio Pereira",
                "number": "100",
                "neighborhood": "Centro",
                "city": "Perdões",
                "state": "MG",
                "zip_code": "37260-000",
                "reference_point": "Centro de Perdões.",
                "latitude": Decimal("-21.092800"),
                "longitude": Decimal("-45.089700"),
            },
            {
                "name": "[DEMO] Lagoa da Pampulha",
                "street": "Avenida Otacílio Negrão de Lima",
                "number": "3000",
                "neighborhood": "Pampulha",
                "city": "Belo Horizonte",
                "state": "MG",
                "zip_code": "31365-450",
                "reference_point": "Praça da Igreja São Francisco.",
                "latitude": Decimal("-19.858400"),
                "longitude": Decimal("-43.979000"),
            },
        )

        locations = []
        for loc_data in real_locations:
            loc_name = loc_data["name"]
            defaults = {k: v for k, v in loc_data.items() if k != "name"}
            location, _ = self.create_if_missing(
                Location,
                {"name": loc_name},
                defaults,
                "locais",
            )
            locations.append(location)

        # (título, modalidade, índice_local, organizador, tipo, status, vagas, preço, inscrições)
        scenarios = (
            # --- Organizador 1: Rafael (demo_organizador) ---
            (
                "Corrida com aprovação",
                "Corrida",
                1,  # Praça Dr. Augusto Silva - Lavras
                "demo_organizador",
                "MANUAL",
                "PUBLISHED",
                10,
                Decimal("0.00"),
                (
                    ("ana", "PENDING", False),
                    ("bruno", "APPROVED", False),
                    ("carla", "REJECTED", False),
                    ("diego", "CANCELED", False),
                ),
            ),
            (
                "Futebol com lista de espera",
                "Futebol",
                0,  # Campo da UFLA - Lavras
                "demo_organizador",
                "AUTO",
                "PUBLISHED",
                2,
                Decimal("15.00"),
                (
                    ("ana", "APPROVED", False),
                    ("bruno", "APPROVED", False),
                    ("carla", "WAITLIST", False),
                ),
            ),
            (
                "Longão 10K no Campus UFLA",
                "Corrida",
                0,  # Campo da UFLA - Lavras
                "demo_organizador",
                "AUTO",
                "PUBLISHED",
                20,
                Decimal("0.00"),
                (("ana", "APPROVED", False), ("diego", "APPROVED", False)),
            ),
            (
                "Giro MTB Serra de Lavras",
                "Ciclismo",
                2,  # Parque Ecológico Quaresmeiras - Lavras
                "demo_organizador",
                "MANUAL",
                "PUBLISHED",
                12,
                Decimal("0.00"),
                (("bruno", "PENDING", False),),
            ),
            # --- Organizador 2: Mariana (demo_organizador2) ---
            (
                "Caminhada com vaga reservada",
                "Caminhada",
                2,  # Parque Ecológico Quaresmeiras - Lavras
                "demo_organizador2",
                "AUTO",
                "PUBLISHED",
                1,
                Decimal("0.00"),
                (("ana", "CANCELED", False), ("diego", "WAITLIST", True)),
            ),
            (
                "Pedal Noturno Nepomuceno",
                "Ciclismo",
                5,  # Praça Padre José - Nepomuceno
                "demo_organizador2",
                "AUTO",
                "PUBLISHED",
                8,
                Decimal("0.00"),
                (("ana", "APPROVED", False), ("bruno", "APPROVED", False)),
            ),
            (
                "Beach Tennis Fim de Tarde",
                "Beach Tennis",
                3,  # Sunset Arena - Lavras
                "demo_organizador2",
                "MANUAL",
                "PUBLISHED",
                4,
                Decimal("25.00"),
                (("carla", "APPROVED", False), ("diego", "PENDING", False)),
            ),
            # --- Organizador 3: Lucas (demo_organizador3) ---
            (
                "Pelada Society Nepomuceno",
                "Futebol",
                4,  # Clube de Nepomuceno
                "demo_organizador3",
                "AUTO",
                "PUBLISHED",
                14,
                Decimal("12.00"),
                (("bruno", "APPROVED", False), ("diego", "APPROVED", False)),
            ),
            (
                "Vôlei de Quadra Misto",
                "Vôlei",
                4,  # Clube de Nepomuceno
                "demo_organizador3",
                "MANUAL",
                "PUBLISHED",
                12,
                Decimal("10.00"),
                (("ana", "PENDING", False), ("carla", "APPROVED", False)),
            ),
            (
                "Treino 5K Parque Novo Horizonte",
                "Corrida",
                6,  # Varginha
                "demo_organizador3",
                "AUTO",
                "PUBLISHED",
                15,
                Decimal("0.00"),
                (("diego", "APPROVED", False),),
            ),
            # --- Organizador 4: Camila (demo_organizador4) ---
            (
                "Torneio Duplas na Areia",
                "Beach Tennis",
                3,  # Sunset Arena - Lavras
                "demo_organizador4",
                "MANUAL",
                "PUBLISHED",
                8,
                Decimal("30.00"),
                (("ana", "APPROVED", False), ("bruno", "PENDING", False)),
            ),
            (
                "Caminhada Matinal em Perdões",
                "Caminhada",
                7,  # Perdões
                "demo_organizador4",
                "AUTO",
                "PUBLISHED",
                25,
                Decimal("0.00"),
                (("ana", "APPROVED", False), ("bruno", "APPROVED", False)),
            ),
            (
                "Volta da Pampulha 18K",
                "Corrida",
                8,  # Belo Horizonte
                "demo_organizador4",
                "MANUAL",
                "PUBLISHED",
                30,
                Decimal("20.00"),
                (("carla", "APPROVED", False), ("diego", "APPROVED", False)),
            ),
            (
                "Vôlei de Praia Recreativo (Rascunho)",
                "Vôlei",
                3,  # Sunset Arena - Lavras
                "demo_organizador4",
                "AUTO",
                "DRAFT",
                8,
                Decimal("15.00"),
                (),
            ),
        )

        scenarios += (
            ("Futebol concluído", "Futebol", 0, "demo_organizador", "AUTO", "FINISHED", 10, Decimal("15.00"),
             (("ana", "APPROVED", False), ("bruno", "APPROVED", False))),
            ("Treino cancelado", "Corrida", 1, "demo_organizador", "AUTO", "CANCELED", 10, Decimal("0.00"), ()),
        )

        for index, (
            title,
            modality,
            location,
            organizer,
            kind,
            status,
            capacity,
            price,
            registrations,
        ) in enumerate(scenarios):
            starts_at = timezone.localtime(self.now).replace(
                hour=8, minute=0, second=0, microsecond=0
            ) + timedelta(days=3 + index)
            if status == "FINISHED":
                starts_at = starts_at - timedelta(days=30 + index)
            activity, created = self.create_if_missing(
                Activity,
                {
                    "title": f"[DEMO] {title}",
                    "organizer": users[organizer],
                },
                {
                    "description": f"Encontro esportivo de {modality.lower()} aberto à comunidade em {locations[location].city}.",
                    "modality": modalities[modality],
                    "location": locations[location],
                    "registration_type": kind,
                    "status": status,
                    "max_participants": capacity,
                    "price": price,
                    "starts_at": starts_at,
                    "ends_at": starts_at + timedelta(hours=2),
                    "confirmation_deadline": starts_at - timedelta(days=1),
                },
                "atividades",
            )
            if not created:
                continue
            for order, (participant, registration_status, offered) in enumerate(
                registrations
            ):
                self.create_registration(
                    activity,
                    users[f"demo_{participant}"],
                    registration_status,
                    offered,
                    order,
                )

        # Add only missing demonstration controls, preserving previous edits.
        finished = Activity.objects.get(title="[DEMO] Futebol concluído", organizer=users["demo_organizador"])
        for username, paid, attended in (("demo_ana", True, True), ("demo_bruno", False, False)):
            registration = Registration.objects.filter(activity=finished, participant=users[username], status="APPROVED").first()
            if registration is None:
                continue
            self.create_if_missing(Payment, {"registration": registration}, {
                "amount": finished.price, "status": "PAID" if paid else "PENDING",
                "method": "PIX", "paid_at": finished.starts_at if paid else None,
            }, "pagamentos")
            self.create_if_missing(Attendance, {"registration": registration}, {
                "attended": attended, "check_in_at": finished.starts_at if attended else None,
                "notes": "Exemplo de presença para a apresentação do C2.",
            }, "presenças")

        expired = Activity.objects.filter(title__startswith="[DEMO]", status="PUBLISHED", confirmation_deadline__lte=self.now).count()
        if expired:
            self.stdout.write(self.style.WARNING(f"Atenção: {expired} atividade(s) demo com prazo encerrado. Datas existentes foram preservadas; ajuste-as pelo Admin antes da apresentação."))

        for category in (
            "usuários",
            "modalidades",
            "locais",
            "atividades",
            "inscrições",
            "notificações",
            "pagamentos",
            "presenças",
        ):
            self.stdout.write(
                f"{category}: {self.created[category]} criado(s); {self.preserved[category]} preservado(s)."
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Demonstração pronta! Contas novas usam a senha informada em --password (padrão: JogaJuntoDemo!2026). Senhas existentes são preservadas."
            )
        )
        self.stdout.write("Contas: " + ", ".join(user[0] for user in DEMO_USERS))

    def create_registration(self, activity, participant, status, offered, order):
        requested_at = min(
            self.now - timedelta(days=2), activity.starts_at - timedelta(days=2)
        ) + timedelta(minutes=order)
        decided_at = (
            requested_at + timedelta(hours=1)
            if status in ("APPROVED", "REJECTED")
            else None
        )
        registration, created = self.create_if_missing(
            Registration,
            {"activity": activity, "participant": participant},
            {
                "status": status,
                "decided_at": decided_at,
                "confirmed_at": decided_at if status == "APPROVED" else None,
                "cancelled_at": (
                    requested_at + timedelta(hours=2) if status == "CANCELED" else None
                ),
                "seat_offered_at": self.now if offered else None,
                "organizer_notes": "Observação interna de demonstração.",
            },
            "inscrições",
        )
        if not created:
            return
        registration.requested_at = requested_at
        Registration.objects.bulk_update([registration], ["requested_at"])
        message = f'Situação de demonstração em "{activity.title}": {registration.get_status_display()}.'
        if offered:
            deadline = timezone.localtime(activity.confirmation_deadline).strftime(
                "%d/%m/%Y às %H:%M"
            )
            message = f'Uma vaga em "{activity.title}" está reservada para você. Confirme em Minhas inscrições até {deadline}.'
        Notification.objects.create(
            recipient=participant, registration=registration, message=message
        )
        self.created["notificações"] += 1
        if status == "PENDING":
            Notification.objects.create(
                recipient=activity.organizer,
                registration=registration,
                message=f'{participant} aguarda sua aprovação em "{activity.title}".',
            )
            self.created["notificações"] += 1
