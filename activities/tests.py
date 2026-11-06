from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.permissions import ensure_access_groups, promote_to_organizer
from registrations.models import Registration

from .admin import ActivityAdmin
from .models import Activity, Location, Modality


def _future_datetimes():
    start = timezone.now() + timedelta(days=2)
    return {
        "starts_at": start,
        "ends_at": start + timedelta(hours=2),
        "confirmation_deadline": start - timedelta(hours=12),
    }


class ActivityFactoryMixin:
    @classmethod
    def setUpTestData(cls):
        ensure_access_groups()
        cls.modality = Modality.objects.create(name="Corrida")
        cls.location = Location.objects.create(
            name="Parque Central",
            street="Rua das Flores",
            neighborhood="Centro",
            city="Lavras",
            state="MG",
            zip_code="37200-000",
        )

    def create_user(self, username, organizer=False):
        user = User.objects.create_user(username=username, password="senha123")
        if organizer:
            promote_to_organizer(user)
            user.refresh_from_db()
        return user

    def create_activity(self, organizer, title="Treino"):
        return Activity.objects.create(
            organizer=organizer,
            modality=self.modality,
            location=self.location,
            title=title,
            description="Atividade de teste",
            max_participants=10,
            price=0,
            status="PUBLISHED",
            **_future_datetimes(),
        )


class ActivityAdminPermissionTests(ActivityFactoryMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = ActivityAdmin(Activity, admin_site=None)

    def _request(self, user):
        request = self.factory.get("/admin/activities/activity/")
        request.user = user
        return request

    def test_organizer_sees_only_own_activities(self):
        owner = self.create_user("dono", organizer=True)
        other = self.create_user("outro", organizer=True)
        own = self.create_activity(owner, "Minha atividade")
        self.create_activity(other, "Atividade alheia")

        queryset = self.admin.get_queryset(self._request(owner))

        self.assertEqual(list(queryset), [own])

    def test_participant_sees_only_registered_activities(self):
        organizer = self.create_user("org", organizer=True)
        participant = self.create_user("part")
        joined = self.create_activity(organizer, "Inscrita")
        self.create_activity(organizer, "Nao inscrita")
        Registration.objects.create(
            activity=joined, participant=participant, status="APPROVED"
        )

        queryset = self.admin.get_queryset(self._request(participant))

        self.assertEqual(list(queryset), [])

    def test_only_owner_can_change_or_delete_activity(self):
        owner = self.create_user("dono", organizer=True)
        other = self.create_user("outro", organizer=True)
        activity = self.create_activity(owner)

        self.assertTrue(
            self.admin.has_change_permission(self._request(owner), activity)
        )
        self.assertTrue(
            self.admin.has_delete_permission(self._request(owner), activity)
        )
        self.assertFalse(
            self.admin.has_change_permission(self._request(other), activity)
        )
        self.assertFalse(
            self.admin.has_delete_permission(self._request(other), activity)
        )


class BaseCatalogAdminTests(ActivityFactoryMixin, TestCase):
    def test_organizer_has_add_links_and_can_open_forms(self):
        user = self.create_user("catalogo_org", organizer=True)
        self.client.force_login(user)
        for model in ("modality", "location"):
            url = reverse(f"admin:activities_{model}_add")
            self.assertContains(
                self.client.get(reverse(f"admin:activities_{model}_changelist")),
                url,
            )
            self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(reverse("admin:activities_modality_add"), {
            "name": "Natação", "description": "", "is_active": "on", "_save": "Salvar",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Modality.objects.filter(name="Natação").exists())

    def test_participant_cannot_add_catalog_entries(self):
        self.client.force_login(self.create_user("catalogo_part"))
        for model in ("modality", "location"):
            self.assertEqual(
                self.client.get(reverse(f"admin:activities_{model}_add")).status_code, 302
            )


class CreateActivityPromotionTests(ActivityFactoryMixin, TestCase):
    def test_organizer_can_create_activity_on_site(self):
        user = self.create_user("novo", organizer=True)
        self.client.force_login(user)

        dates = _future_datetimes()
        response = self.client.post(
            reverse("create_activity"),
            {
                "title": "Pedal da manha",
                "description": "Grupo de ciclismo",
                "modality": self.modality.pk,
                "location": self.location.pk,
                **{f"{name}_{part}": timezone.localtime(value).strftime(fmt)
                   for name, value in dates.items()
                   for part, fmt in ((0, "%Y-%m-%d"), (1, "%H:%M"))},
                "max_participants": 8,
                "price": "0.00",
                "registration_type": "AUTO",
            },
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.has_organizer_group())
        self.assertTrue(Activity.objects.filter(title="Pedal da manha").exists())


class ResubscriptionTests(ActivityFactoryMixin, TestCase):
    def setUp(self):
        self.owner = self.create_user("dono_reinscricao", organizer=True)
        self.person = self.create_user("pessoa_reinscricao")
        self.activity = self.create_activity(self.owner)
        self.registration = Registration.objects.create(activity=self.activity, participant=self.person, status="APPROVED", organizer_notes="Nota preservada")
        self.client.force_login(self.person)
        self.client.post(reverse("cancel_registration", args=[self.registration.pk]))
        self.registration.refresh_from_db()

    def test_automatic_reuses_registration_and_resets_dates(self):
        registration_id = self.registration.pk
        old_requested_at = self.registration.requested_at
        before = timezone.now()
        response = self.client.post(reverse("subscribe_activity", args=[self.activity.pk]), {"source": "mine"}, follow=True)
        self.assertContains(response, "Inscrição confirmada")
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.pk, registration_id)
        self.assertEqual(Registration.objects.filter(activity=self.activity, participant=self.person).count(), 1)
        self.assertEqual(self.registration.status, "APPROVED")
        self.assertIsNone(self.registration.cancelled_at)
        self.assertGreater(self.registration.requested_at, old_requested_at)
        self.assertGreaterEqual(self.registration.confirmed_at, before)
        self.assertEqual(self.registration.organizer_notes, "Nota preservada")
        self.assertTrue(self.person.notifications.filter(message__contains="foi cancelada").exists())
        count = self.person.notifications.count()
        requested_at = self.registration.requested_at
        self.client.post(reverse("subscribe_activity", args=[self.activity.pk]))
        self.registration.refresh_from_db()
        self.assertEqual(self.person.notifications.count(), count)
        self.assertEqual(self.registration.requested_at, requested_at)

    def test_manual_requires_fresh_approval_and_notifies_owner(self):
        self.activity.registration_type = "MANUAL"
        self.activity.save()
        count = self.owner.notifications.count()
        self.assertContains(self.client.get(reverse("home")), "Inscrever-se novamente")
        self.assertContains(self.client.get(reverse("my_registrations")), "Inscrever-se novamente")
        self.client.post(reverse("subscribe_activity", args=[self.activity.pk]))
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, "PENDING")
        self.assertIsNone(self.registration.confirmed_at)
        self.assertIsNone(self.registration.decided_at)
        self.assertIsNone(self.registration.cancelled_at)
        self.assertEqual(self.owner.notifications.count(), count + 1)
        self.assertContains(self.client.get(reverse("my_registrations")), "Pendente de aprovação")
        self.client.force_login(self.owner)
        self.client.post(reverse("decide_registration", args=[self.registration.pk]), {"decision": "APPROVED"})
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, "APPROVED")
        self.assertIsNotNone(self.registration.confirmed_at)

    def test_resubscription_joins_waitlist_when_full_and_rejects_closed_activity(self):
        self.activity.max_participants = 1
        self.activity.save()
        another = self.create_user("outra_pessoa")
        Registration.objects.create(activity=self.activity, participant=another, status="PENDING")
        url = reverse("subscribe_activity", args=[self.activity.pk])
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Você entrou na lista de espera")
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, "WAITLIST")
        self.client.post(reverse("cancel_registration", args=[self.registration.pk]))
        self.activity.max_participants = 10
        self.activity.confirmation_deadline = timezone.now() - timedelta(minutes=1)
        self.activity.save()
        self.client.post(url)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, "CANCELED")
        self.assertNotContains(self.client.get(reverse("my_registrations")), "Inscrever-se novamente")
        self.activity.confirmation_deadline = timezone.now() + timedelta(hours=1)
        self.activity.status = "CANCELED"
        self.activity.save()
        self.client.post(url)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, "CANCELED")


class ActivityValidationTests(ActivityFactoryMixin, TestCase):
    def setUp(self):
        self.owner = self.create_user("validacao", organizer=True)
        self.activity = self.create_activity(self.owner)

    def payload(self, admin=False):
        dates = {name: getattr(self.activity, name) for name in ("starts_at", "ends_at", "confirmation_deadline")}
        data = {
            "title": "Teste de validação", "description": "Atividade de teste",
            "modality": self.modality.pk, "location": self.location.pk,
            "max_participants": 10, "price": "0.00", "registration_type": "AUTO", "status": "PUBLISHED",
        }
        for name, value in dates.items():
            value = timezone.localtime(value).replace(microsecond=0)
            if admin:
                data[f"{name}_0"] = value.strftime("%d/%m/%Y")
                data[f"{name}_1"] = value.strftime("%H:%M:%S")
            else:
                data[f"{name}_0"] = value.strftime("%Y-%m-%d")
                data[f"{name}_1"] = value.strftime("%H:%M:%S")
        if admin:
            data.update({"registrations-TOTAL_FORMS": "0", "registrations-INITIAL_FORMS": "0"})
        return data

    def test_invalid_deadline_is_attached_to_field_in_site_and_admin(self):
        self.client.force_login(self.owner)
        for admin in (False, True):
            for delta in (timedelta(0), timedelta(hours=1)):
                self.activity.confirmation_deadline = self.activity.starts_at + delta
                data = self.payload(admin)
                url = reverse("admin:activities_activity_add") if admin else reverse("create_activity")
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 200)
                form = response.context["adminform"].form if admin else response.context["form"]
                self.assertIn("confirmation_deadline", form.errors)
                self.assertContains(response, "O prazo de confirmação deve ser antes do início")
                self.assertNotContains(response, "check_deadline_before_starts")
                self.assertEqual(form["title"].value(), data["title"])
        self.assertFalse(Activity.objects.filter(title="Teste de validação").exists())

    def test_other_invalid_values_have_field_errors(self):
        from .forms import ActivityForm
        data = self.payload()
        data.update({"ends_at_0": data["starts_at_0"], "ends_at_1": data["starts_at_1"], "max_participants": "0", "price": "-1"})
        form = ActivityForm(data)
        self.assertFalse(form.is_valid())
        for name in ("ends_at", "max_participants", "price"):
            self.assertIn(name, form.errors)
        self.assertNotIn("__all__", form.errors)

    def test_valid_deadline_saves_in_both_forms(self):
        self.client.force_login(self.owner)
        for admin in (False, True):
            data = self.payload(admin)
            data["title"] = f"Atividade válida {admin}"
            response = self.client.post(reverse("admin:activities_activity_add") if admin else reverse("create_activity"), data)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(Activity.objects.filter(title=data["title"]).exists())


class OrganizerDashboardTests(ActivityFactoryMixin, TestCase):
    def test_participant_cannot_open_dashboard(self):
        self.client.force_login(self.create_user("part_dash"))
        response = self.client.get(reverse("organizer_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_organizer_sees_only_own_stats_and_activities(self):
        owner = self.create_user("org_dash", organizer=True)
        other = self.create_user("org_other", organizer=True)
        participant = self.create_user("part_stats")
        own = self.create_activity(owner, "Minha corrida")
        foreign = self.create_activity(other, "Corrida alheia")
        Registration.objects.create(activity=own, participant=participant, status="PENDING")
        Registration.objects.create(
            activity=foreign,
            participant=self.create_user("outro_part"),
            status="APPROVED",
        )

        self.client.force_login(owner)
        response = self.client.get(reverse("organizer_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Minha corrida")
        self.assertNotContains(response, "Corrida alheia")
        self.assertContains(response, "Dashboard")
        self.assertEqual(response.context["pending_total"], 1)
        self.assertEqual(list(response.context["activities"]), [own])
        labels = {card["label"]: card["value"] for card in response.context["cards"]}
        self.assertEqual(labels["Atividades"], 1)
        self.assertEqual(labels["Pendentes"], 1)
        self.assertEqual(labels["Confirmadas"], 0)
