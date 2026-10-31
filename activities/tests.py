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

        self.assertEqual(list(queryset), [joined])

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


class CreateActivityPromotionTests(ActivityFactoryMixin, TestCase):
    def test_creating_activity_on_site_promotes_user(self):
        user = self.create_user("novo")
        self.client.force_login(user)

        dates = _future_datetimes()
        response = self.client.post(
            reverse("create_activity"),
            {
                "title": "Pedal da manha",
                "description": "Grupo de ciclismo",
                "modality": self.modality.pk,
                "location": self.location.pk,
                "starts_at": dates["starts_at"].strftime("%Y-%m-%dT%H:%M"),
                "ends_at": dates["ends_at"].strftime("%Y-%m-%dT%H:%M"),
                "max_participants": 8,
                "price": "0.00",
                "confirmation_deadline": dates["confirmation_deadline"].strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "registration_type": "AUTO",
            },
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.has_organizer_group())
        self.assertTrue(Activity.objects.filter(title="Pedal da manha").exists())
