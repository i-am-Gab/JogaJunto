from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from registrations.models import Registration
from .tests import ActivityFactoryMixin


class ActivityDetailTests(ActivityFactoryMixin, TestCase):
    def setUp(self):
        self.owner = self.create_user("owner", organizer=True)
        self.participant = self.create_user("participant")
        self.activity = self.create_activity(self.owner, "Corrida na praça")
        self.url = reverse("activity_detail", args=[self.activity.pk])

    def test_public_detail_and_login_return_to_same_activity(self):
        response = self.client.get(self.url)
        self.assertContains(response, self.activity.description)
        self.assertContains(response, self.activity.location.street)
        self.assertContains(response, "10 disponíveis")
        self.assertContains(response, "next=" + self.url)
        self.assertContains(self.client.get(reverse("home")), f'href="{self.url}"')
        self.assertEqual(Registration.objects.count(), 0)
        response = self.client.post(reverse("login") + "?next=" + self.url, {
            "username": self.participant.username, "password": "senha123", "next": self.url,
        })
        self.assertRedirects(response, self.url)

    def test_draft_is_private_even_when_posting_subscription(self):
        self.activity.status = "DRAFT"
        self.activity.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.force_login(self.participant)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.post(reverse("subscribe_activity", args=[self.activity.pk]), {"source": "detail"})
        self.assertFalse(self.activity.registrations.exists())
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(self.url), "Gerenciar inscrições")

    def test_inscription_redirects_to_detail_and_cannot_duplicate(self):
        self.client.force_login(self.participant)
        subscribe = reverse("subscribe_activity", args=[self.activity.pk])
        response = self.client.post(subscribe, {"source": "detail"})
        self.assertRedirects(response, self.url)
        self.assertContains(self.client.get(self.url), "Sua inscrição: Aprovada")
        self.client.post(subscribe, {"source": "detail"})
        self.assertEqual(self.activity.registrations.count(), 1)

    def test_reserved_and_pending_seats_count_and_queue_subscription(self):
        self.activity.max_participants = 2
        self.activity.save()
        Registration.objects.create(activity=self.activity, participant=self.create_user("pending"), status="PENDING")
        Registration.objects.create(activity=self.activity, participant=self.create_user("reserved"), status="WAITLIST", seat_offered_at=timezone.now())
        self.client.force_login(self.participant)
        response = self.client.get(self.url)
        self.assertContains(response, "0 disponíveis")
        self.assertContains(response, "Entrar na lista de espera")
        self.client.post(reverse("subscribe_activity", args=[self.activity.pk]), {"source": "detail"})
        self.assertEqual(Registration.objects.get(participant=self.participant).status, "WAITLIST")

    def test_closed_activity_and_csrf_protection(self):
        self.activity.confirmation_deadline = timezone.now() - timedelta(minutes=1)
        self.activity.save()
        self.client.force_login(self.participant)
        self.assertContains(self.client.get(self.url), "Inscrições encerradas")
        self.client.post(reverse("subscribe_activity", args=[self.activity.pk]), {"source": "detail"})
        self.assertFalse(self.activity.registrations.exists())
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.participant)
        self.assertEqual(client.post(reverse("subscribe_activity", args=[self.activity.pk])).status_code, 403)

    def test_manual_request_and_reserved_seat_actions(self):
        self.activity.registration_type = "MANUAL"
        self.activity.save()
        self.client.force_login(self.participant)
        self.assertContains(self.client.get(self.url), "Solicitar inscrição")
        self.client.post(reverse("subscribe_activity", args=[self.activity.pk]), {"source": "detail"})
        self.assertContains(self.client.get(self.url), "Sua inscrição: Pendente")
        registration = self.activity.registrations.get(participant=self.participant)
        registration.status = "WAITLIST"
        registration.seat_offered_at = timezone.now()
        registration.save()
        self.assertContains(self.client.get(self.url), "Confirmar vaga reservada")
        self.client.post(reverse("confirm_waitlist_seat", args=[registration.pk]))
        registration.refresh_from_db()
        self.assertEqual(registration.status, "PENDING")
