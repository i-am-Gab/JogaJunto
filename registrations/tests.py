from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils import timezone

from accounts.models import User
from accounts.permissions import ensure_access_groups, promote_to_organizer
from activities.models import Activity, Location, Modality

from .admin import RegistrationAdmin
from .models import Registration


class RegistrationAdminScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_access_groups()
        cls.modality = Modality.objects.create(name="Futebol")
        cls.location = Location.objects.create(
            name="Quadra 1",
            street="Av. Principal",
            neighborhood="Centro",
            city="Lavras",
            state="MG",
            zip_code="37200-000",
        )
        start = timezone.now() + timedelta(days=3)
        cls.owner = User.objects.create_user(username="org1", password="senha123")
        promote_to_organizer(cls.owner)
        cls.other_org = User.objects.create_user(username="org2", password="senha123")
        promote_to_organizer(cls.other_org)
        cls.participant = User.objects.create_user(username="jog", password="senha123")

        cls.own_activity = Activity.objects.create(
            organizer=cls.owner,
            modality=cls.modality,
            location=cls.location,
            title="Rachao",
            description="Jogo semanal",
            starts_at=start,
            ends_at=start + timedelta(hours=2),
            confirmation_deadline=start - timedelta(hours=6),
            max_participants=12,
            status="PUBLISHED",
        )
        cls.other_activity = Activity.objects.create(
            organizer=cls.other_org,
            modality=cls.modality,
            location=cls.location,
            title="Outro jogo",
            description="Outro grupo",
            starts_at=start,
            ends_at=start + timedelta(hours=2),
            confirmation_deadline=start - timedelta(hours=6),
            max_participants=12,
            status="PUBLISHED",
        )
        cls.own_registration = Registration.objects.create(
            activity=cls.own_activity,
            participant=cls.participant,
            status="APPROVED",
        )
        cls.other_registration = Registration.objects.create(
            activity=cls.other_activity,
            participant=cls.other_org,
            status="APPROVED",
        )

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = RegistrationAdmin(Registration, admin_site=None)

    def _request(self, user):
        request = self.factory.get("/admin/registrations/registration/")
        request.user = user
        return request

    def test_organizer_sees_only_own_activity_registrations(self):
        queryset = self.admin.get_queryset(self._request(self.owner))
        self.assertEqual(list(queryset), [self.own_registration])

    def test_participant_sees_own_registration(self):
        queryset = self.admin.get_queryset(self._request(self.participant))
        self.assertEqual(list(queryset), [self.own_registration])

    def test_organizer_cannot_change_registration_of_other_activity(self):
        self.assertTrue(
            self.admin.has_change_permission(
                self._request(self.owner), self.own_registration
            )
        )
        self.assertFalse(
            self.admin.has_change_permission(
                self._request(self.owner), self.other_registration
            )
        )
