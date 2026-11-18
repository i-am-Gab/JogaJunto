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


    def increase_capacity(self, capacity=2):
        self.activity.max_participants = capacity
        self.activity.save(update_fields=["max_participants"])
        self.wait1.refresh_from_db()
        self.wait2.refresh_from_db()

    def test_capacity_increase_offers_only_available_places_in_queue_order(self):
        self.increase_capacity()
        self.assertIsNotNone(self.wait1.seat_offered_at)
        self.assertIsNone(self.wait2.seat_offered_at)
        self.assertEqual(occupied_seats(self.activity.registrations).count(), 2)
        self.assertEqual(self.first.notifications.filter(message__contains="reservada para você").count(), 1)
        self.activity.save()
        self.assertEqual(self.first.notifications.filter(message__contains="reservada para você").count(), 1)
        self.increase_capacity(3)
        self.assertIsNotNone(self.wait2.seat_offered_at)
        self.assertEqual(occupied_seats(self.activity.registrations).count(), 3)

    def test_owner_can_approve_reserved_waitlist_from_review_and_admin(self):
        self.increase_capacity()
        self.client.force_login(self.owner)
        review = reverse("review_registrations")
        response = self.client.get(review, {"situacao": "WAITLIST", "atividade": self.activity.pk})
        self.assertContains(response, "Lista de espera")
        self.assertContains(response, "Aprovar inscrição", count=1)
        self.assertContains(response, "Vaga reservada por ordem da fila")
        self.assertContains(self.client.get(reverse("admin:activities_activity_change", args=[self.activity.pk])), "Aprovar inscrição")
        self.assertEqual(response.context["tabs"][1]["count"], 2)
        url = reverse("decide_registration", args=[self.wait1.pk])
        before = self.first.notifications.count()
        self.client.post(url, {"decision": "APPROVED", "organizer_notes": "Vaga extra"})
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "APPROVED")
        self.assertIsNone(self.wait1.seat_offered_at)
        self.assertIsNotNone(self.wait1.confirmed_at)
        self.assertEqual(self.wait1.organizer_notes, "Vaga extra")
        self.assertEqual(self.first.notifications.count(), before + 1)
        self.client.post(url, {"decision": "APPROVED"})
        self.assertEqual(self.first.notifications.count(), before + 1)
        self.client.force_login(self.first)
        self.assertContains(self.client.get(reverse("my_registrations")), "Inscrição confirmada")

    def test_queue_cannot_be_skipped_even_with_forged_approval(self):
        self.increase_capacity()
        self.client.force_login(self.owner)
        response = self.client.post(reverse("decide_registration", args=[self.wait2.pk]), {"decision": "APPROVED"}, follow=True)
        self.assertContains(response, "ainda não tem uma vaga reservada")
        self.wait2.refresh_from_db()
        self.assertEqual(self.wait2.status, "WAITLIST")
        self.assertEqual(occupied_seats(self.activity.registrations).count(), 2)

    def test_capacity_reduction_prevents_approval_using_stale_offer(self):
        self.increase_capacity()
        self.activity.max_participants = 1
        self.activity.save()
        self.client.force_login(self.owner)
        response = self.client.post(reverse("decide_registration", args=[self.wait1.pk]), {"decision": "APPROVED"}, follow=True)
        self.assertContains(response, "Não há vagas disponíveis")
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "WAITLIST")

    def test_increase_after_deadline_does_not_offer_or_approve(self):
        self.activity.confirmation_deadline = timezone.now() - timedelta(seconds=1)
        self.activity.save()
        self.increase_capacity()
        self.assertIsNone(self.wait1.seat_offered_at)
        self.client.force_login(self.owner)
        self.client.post(reverse("decide_registration", args=[self.wait1.pk]), {"decision": "APPROVED"})
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "WAITLIST")

    def test_expired_or_canceled_offer_cannot_be_approved(self):
        self.increase_capacity()
        for changes in ({"confirmation_deadline": timezone.now() - timedelta(seconds=1)}, {"status": "CANCELED"}):
            Activity.objects.filter(pk=self.activity.pk).update(**changes)
            self.client.force_login(self.owner)
            self.assertNotContains(self.client.get(reverse("review_registrations"), {"situacao": "WAITLIST"}), "Aprovar inscrição")
            self.client.post(reverse("decide_registration", args=[self.wait1.pk]), {"decision": "APPROVED"})
            self.wait1.refresh_from_db()
            self.assertEqual(self.wait1.status, "WAITLIST")

    def test_participant_or_another_organizer_cannot_approve_reserved_place(self):
        self.increase_capacity()
        url = reverse("decide_registration", args=[self.wait1.pk])
        self.client.force_login(self.first)
        self.assertEqual(self.client.post(url, {"decision": "APPROVED"}).status_code, 403)
        other = User.objects.create_user(username="other_owner", role="organizador")
        self.client.force_login(other)
        self.assertEqual(self.client.post(url, {"decision": "APPROVED"}).status_code, 404)

    def test_reject_reserved_request_releases_place_for_next_person(self):
        self.increase_capacity()
        self.client.force_login(self.owner)
        self.client.post(reverse("decide_registration", args=[self.wait1.pk]), {"decision": "REJECTED"})
        self.wait1.refresh_from_db()
        self.wait2.refresh_from_db()
        self.assertEqual(self.wait1.status, "REJECTED")
        self.assertIsNone(self.wait1.seat_offered_at)
        self.assertIsNotNone(self.wait2.seat_offered_at)

    def test_approval_respects_pending_and_reserved_places(self):
        self.increase_capacity()
        extra = User.objects.create_user(username="extra_pending")
        Registration.objects.create(activity=self.activity, participant=extra, status="PENDING")
        self.client.force_login(self.owner)
        response = self.client.post(reverse("decide_registration", args=[self.wait1.pk]), {"decision": "APPROVED"}, follow=True)
        self.assertContains(response, "Não há vagas disponíveis")
        self.wait1.refresh_from_db()
        self.assertEqual(self.wait1.status, "WAITLIST")

    def test_unsaved_capacity_change_does_not_trigger_offer(self):
        self.activity.max_participants = 2
        self.activity.title = "Novo título"
        self.activity.save(update_fields=["title"])
        self.wait1.refresh_from_db()
        self.assertIsNone(self.wait1.seat_offered_at)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.max_participants, 1)

    def test_admin_capacity_edit_reserves_and_exposes_approval_button(self):
        self.client.force_login(self.owner)
        url = reverse("admin:activities_activity_change", args=[self.activity.pk])
        response = self.client.get(url)
        formset = response.context["inline_admin_formsets"][0].formset
        prefix = formset.prefix
        data = {
            "title": self.activity.title, "description": self.activity.description,
            "modality": self.activity.modality_id, "location": self.activity.location_id,
            "max_participants": 2, "price": "0.00", "registration_type": "AUTO",
            "status": "PUBLISHED", "_continue": "Salvar e continuar",
            f"{prefix}-TOTAL_FORMS": len(formset.forms),
            f"{prefix}-INITIAL_FORMS": len(formset.initial_forms),
            f"{prefix}-MIN_NUM_FORMS": 0, f"{prefix}-MAX_NUM_FORMS": 1000,
        }
        for field in ("starts_at", "ends_at", "confirmation_deadline"):
            value = timezone.localtime(getattr(self.activity, field))
            data[f"{field}_0"] = value.strftime("%Y-%m-%d")
            data[f"{field}_1"] = value.strftime("%H:%M:%S")
        for index, form in enumerate(formset.forms):
            data[f"{prefix}-{index}-id"] = form.instance.pk
            data[f"{prefix}-{index}-activity"] = self.activity.pk
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.activity.refresh_from_db()
        self.wait1.refresh_from_db()
        self.assertEqual(self.activity.max_participants, 2)
        self.assertIsNotNone(self.wait1.seat_offered_at)
        self.assertContains(response, "Aprovar inscrição", count=1)
