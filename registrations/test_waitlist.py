from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from activities.models import Activity, Location, Modality
from .models import Notification, Registration
from .waitlist import offer_available_seats, occupied_seats


class WaitlistFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="organizador", role="organizador")
        self.holder = User.objects.create_user(username="inscrito")
        self.first = User.objects.create_user(username="primeiro")
        self.second = User.objects.create_user(username="segundo")
        self.start = timezone.now() + timedelta(days=3)
        self.activity = Activity.objects.create(
            title="Corrida com fila", description="Treino", organizer=self.owner,
            modality=Modality.objects.create(name="Corrida"),
            location=Location.objects.create(name="Parque", city="Lavras", state="MG"),
            starts_at=self.start, ends_at=self.start + timedelta(hours=2),
            confirmation_deadline=self.start - timedelta(hours=1),
            max_participants=1, status="PUBLISHED", registration_type="AUTO",
        )
        self.registration = Registration.objects.create(activity=self.activity, participant=self.holder, status="APPROVED")
        for user in (self.first, self.second):
            self.client.force_login(user)
            self.client.post(reverse("subscribe_activity", args=[self.activity.pk]))
        self.wait1 = Registration.objects.get(participant=self.first)
        self.wait2 = Registration.objects.get(participant=self.second)

    def release(self):
        self.client.force_login(self.holder)
        return self.client.post(reverse("cancel_registration", args=[self.registration.pk]))

    def test_cancel_reserves_only_for_first_in_line_and_notifies_once(self):
        self.assertEqual(self.wait1.status, "WAITLIST")
        self.assertIsNone(self.wait1.seat_offered_at)
        self.release()
        self.wait1.refresh_from_db()
        self.wait2.refresh_from_db()
        self.assertIsNotNone(self.wait1.seat_offered_at)
        self.assertIsNone(self.wait2.seat_offered_at)
        self.assertEqual(occupied_seats(self.activity.registrations).count(), 1)
        self.assertEqual(self.first.notifications.filter(message__contains="reservada para você").count(), 1)
        offer_available_seats(self.activity.pk)
        self.release()
        self.assertEqual(self.first.notifications.filter(message__contains="reservada para você").count(), 1)
        self.assertFalse(self.second.notifications.filter(message__contains="reservada para você").exists())
        self.client.force_login(self.first)
        self.assertContains(self.client.get(reverse("my_registrations")), "Confirmar minha vaga")

    def test_offer_cannot_be_stolen_and_confirmation_is_private_and_idempotent(self):
        self.release()
        newcomer = User.objects.create_user(username="novo")
        self.client.force_login(newcomer)
        self.client.post(reverse("subscribe_activity", args=[self.activity.pk]))
        self.assertEqual(Registration.objects.get(participant=newcomer).status, "WAITLIST")
        url = reverse("confirm_waitlist_seat", args=[self.wait1.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_login(self.second)
        self.client.post(reverse("confirm_waitlist_seat", args=[self.wait2.pk]))
        self.wait2.refresh_from_db()
        self.assertEqual(self.wait2.status, "WAITLIST")
        self.client.force_login(self.first)
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, follow=True)
        self.assertContains(response, "Sua inscrição está confirmada")
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "APPROVED")
        self.assertIsNotNone(self.wait1.confirmed_at)
        count = self.first.notifications.count()
        self.client.post(url)
        self.assertEqual(self.first.notifications.count(), count)
        self.assertEqual(occupied_seats(self.activity.registrations).count(), 1)

    def test_declining_offer_by_cancelling_moves_to_next(self):
        self.release()
        self.client.force_login(self.first)
        self.client.post(reverse("cancel_registration", args=[self.wait1.pk]))
        self.wait1.refresh_from_db()
        self.wait2.refresh_from_db()
        self.assertEqual(self.wait1.status, "CANCELED")
        self.assertIsNone(self.wait1.seat_offered_at)
        self.assertIsNotNone(self.wait2.seat_offered_at)
        self.assertTrue(self.second.notifications.filter(message__contains="reservada para você").exists())

    def test_manual_activity_requires_approval_after_acceptance(self):
        self.activity.registration_type = "MANUAL"
        self.activity.save()
        self.release()
        self.client.force_login(self.first)
        self.client.post(reverse("confirm_waitlist_seat", args=[self.wait1.pk]))
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "PENDING")
        self.assertIsNone(self.wait1.confirmed_at)
        self.assertTrue(self.owner.notifications.filter(registration=self.wait1, message__contains="Aguardando sua aprovação").exists())
        self.client.force_login(self.owner)
        self.client.post(reverse("decide_registration", args=[self.wait1.pk]), {"decision": "APPROVED"})
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "APPROVED")

    def test_deadline_prevents_confirmation_and_new_offers(self):
        self.release()
        self.activity.confirmation_deadline = timezone.now() - timedelta(seconds=1)
        self.activity.save()
        self.client.force_login(self.first)
        self.client.post(reverse("confirm_waitlist_seat", args=[self.wait1.pk]))
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "WAITLIST")
        self.assertNotContains(self.client.get(reverse("my_registrations")), "Confirmar minha vaga")
        self.client.post(reverse("cancel_registration", args=[self.wait1.pk]))
        self.wait2.refresh_from_db()
        self.assertIsNone(self.wait2.seat_offered_at)
