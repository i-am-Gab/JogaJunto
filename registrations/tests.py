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

    def test_manual_subscription_and_admin_approval_notify_participant(self):
        from .models import Notification
        self.own_activity.registration_type = "MANUAL"
        self.own_activity.save()
        applicant = User.objects.create_user(username="solicitante", password="senha123")
        self.client.force_login(applicant)
        response = self.client.post(reverse("subscribe_activity", args=[self.own_activity.pk]), follow=True)
        self.assertContains(response, "Pendente de aprovação")
        self.assertNotContains(response, "Inscrição confirmada")
        registration = Registration.objects.get(participant=applicant)
        self.assertEqual(registration.status, "PENDING")
        self.assertTrue(applicant.notifications.filter(message__contains="pendente de aprovação").exists())
        self.assertTrue(self.owner.notifications.filter(registration=registration).exists())
        self.client.force_login(self.owner)
        response = self.client.post(reverse("admin:registrations_registration_change", args=[registration.pk]), {
            "activity": self.own_activity.pk, "participant": applicant.pk,
            "status": "APPROVED", "_save": "Salvar",
        })
        self.assertEqual(response.status_code, 302)
        registration.refresh_from_db()
        self.assertEqual(registration.status, "APPROVED")
        self.assertTrue(Notification.objects.filter(recipient=applicant, message__contains="foi aprovada").exists())
        self.client.force_login(applicant)
        self.assertContains(self.client.get(reverse("home")), "Inscrição confirmada")
        self.assertContains(self.client.get(reverse("notifications")), "foi aprovada")

    def test_auto_subscription_is_confirmed_and_notifies_once(self):
        user = User.objects.create_user(username="auto")
        self.client.force_login(user)
        url = reverse("subscribe_activity", args=[self.own_activity.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        registration = Registration.objects.get(participant=user)
        self.assertEqual(registration.status, "APPROVED")
        self.client.post(url)
        registration.organizer_notes = "Sem alteração de situação"
        registration.save()
        self.assertEqual(user.notifications.count(), 1)

    def test_notifications_are_private_and_read_requires_post(self):
        mine = self.participant.notifications.first()
        self.client.force_login(self.other_org)
        url = reverse("read_notification", args=[mine.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertNotContains(self.client.get(reverse("notifications")), self.own_activity.title)
        self.client.force_login(self.participant)
        self.assertEqual(self.client.post(url).status_code, 302)
        mine.refresh_from_db()
        self.assertIsNotNone(mine.read_at)
        self.assertEqual(self.client.post(reverse("read_all_notifications")).status_code, 302)
        self.assertFalse(self.participant.notifications.filter(read_at__isnull=True).exists())

    def test_rejection_waitlist_cancellation_are_not_confirmed(self):
        self.client.force_login(self.participant)
        for status, text in (("REJECTED", "Inscrição rejeitada"), ("WAITLIST", "Na lista de espera"), ("CANCELED", "Inscrição cancelada")):
            self.own_registration.status = status
            self.own_registration.save()
            response = self.client.get(reverse("home"))
            self.assertContains(response, text)
            self.assertNotContains(response, "Inscrição confirmada")

    def test_review_page_scopes_requests_and_filters(self):
        self.own_registration.status = "PENDING"
        self.own_registration.save()
        self.client.force_login(self.owner)
        response = self.client.get(reverse("review_registrations"))
        self.assertContains(response, "Aprovar inscrição")
        self.assertContains(response, self.own_activity.title)
        self.assertNotContains(response, self.other_activity.title)
        self.assertEqual(self.client.get(reverse("review_registrations"), {"atividade": self.other_activity.pk}).status_code, 404)
        self.assertEqual(self.client.get(reverse("review_registrations"), {"atividade": "invalida"}).status_code, 404)

    def test_decision_notifies_once_and_records_time(self):
        self.own_registration.status = "PENDING"
        self.own_registration.save()
        self.client.force_login(self.owner)
        url = reverse("decide_registration", args=[self.own_registration.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url, {"decision": "INVALID"}).status_code, 400)
        before = self.participant.notifications.count()
        response = self.client.post(url, {"decision": "APPROVED"}, follow=True)
        self.assertContains(response, "O participante foi notificado")
        self.own_registration.refresh_from_db()
        self.assertEqual(self.own_registration.status, "APPROVED")
        self.assertIsNotNone(self.own_registration.decided_at)
        self.client.post(url, {"decision": "REJECTED"})
        self.own_registration.refresh_from_db()
        self.assertEqual(self.own_registration.status, "APPROVED")
        self.assertEqual(self.participant.notifications.count(), before + 1)

    def test_participant_and_other_organizer_cannot_decide(self):
        url = reverse("decide_registration", args=[self.own_registration.pk])
        self.client.force_login(self.participant)
        self.assertEqual(self.client.get(reverse("review_registrations")).status_code, 403)
        self.assertEqual(self.client.post(url, {"decision": "APPROVED"}).status_code, 403)
        self.client.force_login(self.other_org)
        self.assertEqual(self.client.post(url, {"decision": "APPROVED"}).status_code, 404)

    def test_rejection_and_full_capacity(self):
        self.own_activity.max_participants = 1
        self.own_activity.save()
        pending = Registration.objects.create(activity=self.own_activity, participant=self.other_org, status="PENDING")
        self.client.force_login(self.owner)
        url = reverse("decide_registration", args=[pending.pk])
        response = self.client.post(url, {"decision": "APPROVED"}, follow=True)
        self.assertContains(response, "Não há vagas disponíveis")
        pending.refresh_from_db()
        self.assertEqual(pending.status, "PENDING")
        self.client.post(url, {"decision": "REJECTED"})
        pending.refresh_from_db()
        self.assertEqual(pending.status, "REJECTED")
        self.assertTrue(self.other_org.notifications.filter(registration=pending, message__contains="rejeitada").exists())

    def test_approval_fills_dates_and_saves_notes(self):
        pending = Registration.objects.create(activity=self.own_activity, participant=self.other_org, status="PENDING")
        self.client.force_login(self.owner)
        before = timezone.now()
        self.client.post(reverse("decide_registration", args=[pending.pk]), {
            "decision": "APPROVED", "organizer_notes": "  Trazer documento  ",
            "decided_at": "2000-01-01", "confirmed_at": "2000-01-01", "source": "activity",
        })
        pending.refresh_from_db()
        self.assertEqual(pending.organizer_notes, "Trazer documento")
        self.assertEqual(pending.decided_at, pending.confirmed_at)
        self.assertGreaterEqual(pending.confirmed_at, before)
        notifications = pending.notifications.count()
        self.client.post(reverse("decide_registration", args=[pending.pk]), {
            "decision": "SAVE_NOTES", "organizer_notes": "Documento conferido",
        })
        decided_at, confirmed_at = pending.decided_at, pending.confirmed_at
        pending.refresh_from_db()
        self.assertEqual(pending.status, "APPROVED")
        self.assertEqual(pending.decided_at, decided_at)
        self.assertEqual(pending.confirmed_at, confirmed_at)
        self.assertEqual(pending.notifications.count(), notifications)
        self.assertEqual(pending.organizer_notes, "Documento conferido")

    def test_notes_remain_private_and_foreign_updates_are_denied(self):
        self.client.force_login(self.owner)
        url = reverse("decide_registration", args=[self.other_registration.pk])
        self.assertEqual(self.client.post(url, {"decision": "SAVE_NOTES", "organizer_notes": "Não autorizado"}).status_code, 404)
        self.own_registration.organizer_notes = "Nota interna confidencial"
        self.own_registration.save(update_fields=["organizer_notes"])
        self.client.force_login(self.participant)
        url = reverse("decide_registration", args=[self.own_registration.pk])
        self.assertEqual(self.client.post(url, {"decision": "SAVE_NOTES"}).status_code, 403)
        self.assertNotContains(self.client.get(reverse("notifications")), "Nota interna confidencial")

    def test_activity_inline_has_actions_details_and_no_editable_dates(self):
        self.client.force_login(self.owner)
        self.own_registration.status = "PENDING"
        self.own_registration.save()
        response = self.client.get(reverse("admin:activities_activity_change", args=[self.own_activity.pk]))
        self.assertContains(response, "Aprovar inscrição")
        self.assertContains(response, "<summary>Ver informações</summary>", html=True)
        self.assertContains(response, f'id="registration-action-{self.own_registration.pk}"')
        self.assertContains(response, f'form="registration-action-{self.own_registration.pk}"')
        self.assertNotContains(response, 'name="registrations-0-decided_at_0"')
        self.assertNotContains(response, 'name="registrations-0-confirmed_at_0"')

    def test_admin_dates_are_read_only_and_set_on_status_change(self):
        pending = Registration.objects.create(activity=self.own_activity, participant=self.other_org, status="PENDING")
        self.client.force_login(self.owner)
        url = reverse("admin:registrations_registration_change", args=[pending.pk])
        response = self.client.get(url)
        for name in ("requested_at", "decided_at", "confirmed_at", "cancelled_at"):
            self.assertNotIn(name, response.context["adminform"].form.fields)
        self.client.post(url, {"activity": self.own_activity.pk, "participant": self.other_org.pk, "status": "APPROVED", "_save": "Salvar"})
        pending.refresh_from_db()
        self.assertIsNotNone(pending.decided_at)
        self.assertEqual(pending.confirmed_at, pending.decided_at)

    def test_my_registrations_are_private_and_show_status(self):
        self.own_registration.organizer_notes = "Observação interna secreta"
        self.own_registration.save(update_fields=["organizer_notes"])
        self.client.force_login(self.participant)
        response = self.client.get(reverse("my_registrations"))
        self.assertContains(response, self.own_activity.title)
        self.assertContains(response, "Inscrição confirmada")
        self.assertContains(response, "Cancelar inscrição")
        self.assertNotContains(response, self.other_activity.title)
        self.assertNotContains(response, "Observação interna secreta")
        self.assertEqual(list(response.context["page_obj"]), [self.own_registration])
        for status, text in (("PENDING", "Pendente de aprovação"), ("WAITLIST", "Lista de Espera"), ("REJECTED", "Rejeitada"), ("CANCELED", "Cancelada")):
            self.own_registration.status = status
            self.own_registration.save()
            self.assertContains(self.client.get(reverse("my_registrations")), text)

    def test_cancel_is_owned_post_only_and_notifies_once(self):
        self.client.force_login(self.participant)
        url = reverse("cancel_registration", args=[self.own_registration.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        foreign = reverse("cancel_registration", args=[self.other_registration.pk])
        self.assertEqual(self.client.post(foreign).status_code, 404)
        before = self.owner.notifications.count()
        response = self.client.post(url, follow=True)
        self.assertContains(response, "O organizador foi notificado")
        self.own_registration.refresh_from_db()
        cancelled_at = self.own_registration.cancelled_at
        self.assertEqual(self.own_registration.status, "CANCELED")
        self.assertIsNotNone(cancelled_at)
        self.assertEqual(self.owner.notifications.count(), before + 1)
        self.assertNotContains(response, "Confirmar cancelamento")
        self.client.post(url)
        self.own_registration.refresh_from_db()
        self.assertEqual(self.own_registration.cancelled_at, cancelled_at)
        self.assertEqual(self.owner.notifications.count(), before + 1)
        self.assertContains(self.client.get(reverse("home")), "0 de 12 vagas")

    def test_cancel_pending_or_waiting_and_block_started_activity(self):
        self.client.force_login(self.participant)
        url = reverse("cancel_registration", args=[self.own_registration.pk])
        for status in ("PENDING", "WAITLIST"):
            self.own_registration.status = status
            self.own_registration.save()
            self.client.post(url)
            self.own_registration.refresh_from_db()
            self.assertEqual(self.own_registration.status, "CANCELED")
        self.own_registration.status = "APPROVED"
        self.own_registration.save()
        self.own_activity.starts_at = timezone.now() - timedelta(hours=1)
        self.own_activity.confirmation_deadline = timezone.now() - timedelta(hours=2)
        self.own_activity.save()
        self.client.post(url)
        self.own_registration.refresh_from_db()
        self.assertEqual(self.own_registration.status, "APPROVED")
        self.assertNotContains(self.client.get(reverse("my_registrations")), "Confirmar cancelamento")

    def test_my_registrations_filter_and_login_required(self):
        self.assertEqual(self.client.get(reverse("my_registrations")).status_code, 302)
        self.assertEqual(self.client.post(reverse("cancel_registration", args=[self.own_registration.pk])).status_code, 302)
        self.client.force_login(self.participant)
        response = self.client.get(reverse("my_registrations"), {"situacao": "PENDING"})
        self.assertEqual(len(response.context["page_obj"]), 0)
        self.assertContains(response, "Nenhuma inscrição")
        response = self.client.get(reverse("my_registrations"), {"situacao": "INVALID"})
        self.assertEqual(response.context["selected"], "ALL")
        self.assertContains(self.client.get(reverse("home")), reverse("my_registrations"))
