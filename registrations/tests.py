from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from accounts.models import User
from accounts.permissions import ensure_access_groups, promote_to_organizer
from activities.models import Activity, Location, Modality

from .admin import RegistrationAdmin
from .models import Registration, Payment, Attendance
from django.urls import reverse


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

    def test_participant_has_no_admin_queryset(self):
        queryset = self.admin.get_queryset(self._request(self.participant))
        self.assertEqual(list(queryset), [])

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

    def test_organizer_cannot_read_or_post_other_activity_objects(self):
        self.client.force_login(self.owner)
        payment = Payment.objects.create(registration=self.other_registration, amount=10, status="PENDING", method="PIX")
        attendance = Attendance.objects.create(registration=self.other_registration)
        for model, obj in (("registration", self.other_registration), ("payment", payment), ("attendance", attendance)):
            url = reverse(f"admin:registrations_{model}_change", args=[obj.pk])
            for response in (self.client.get(url), self.client.post(url, {"status": "APPROVED"})):
                self.assertIn(response.status_code, (302, 403, 404))
        payment.refresh_from_db()
        self.assertEqual(payment.status, "PENDING")

    def test_foreign_key_choices_reject_other_organizers_records(self):
        from django.contrib import admin
        from .admin import PaymentAdmin, AttendanceAdmin
        request = self._request(self.owner)
        for model, admin_class in ((Payment, PaymentAdmin), (Attendance, AttendanceAdmin)):
            form = admin_class(model, admin.site).get_form(request)()
            self.assertIn(self.own_registration, form.fields["registration"].queryset)
            self.assertNotIn(self.other_registration, form.fields["registration"].queryset)
            with self.assertRaises(ValidationError):
                form.fields["registration"].clean(self.other_registration.pk)
        field = self.admin.formfield_for_foreignkey(Registration._meta.get_field("activity"), request)
        self.assertNotIn(self.other_activity, field.queryset)

    def test_organizer_cannot_see_other_activity_even_as_participant(self):
        Registration.objects.create(activity=self.other_activity, participant=self.owner)
        self.assertEqual(list(self.admin.get_queryset(self._request(self.owner))), [self.own_registration])
