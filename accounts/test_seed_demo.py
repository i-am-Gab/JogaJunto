from io import StringIO
from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from activities.models import Activity, Location, Modality
from registrations.models import Registration, Notification
from registrations.waitlist import occupied_seats
from .management.commands.seed_demo import DEMO_PASSWORD


class SeedDemoTests(TestCase):
    models = (User, Group, Permission, Modality, Location, Activity, Registration, Notification,
              User.groups.through, User.user_permissions.through, Group.permissions.through)

    def seed(self, **options):
        output = StringIO()
        call_command("seed_demo", stdout=output, **options)
        return output.getvalue()

    def snapshot(self):
        return {model: list(model.objects.order_by("pk").values()) for model in self.models}

    def assert_preserved(self, snapshot):
        for model, rows in snapshot.items():
            self.assertEqual(list(model.objects.filter(pk__in=[row["id"] for row in rows]).order_by("pk").values()), rows, model.__name__)

    def test_creates_usable_users_and_all_scenarios(self):
        self.seed()
        self.assertEqual(User.objects.count(), 7)
        self.assertEqual(Modality.objects.count(), 4)
        self.assertEqual(Location.objects.count(), 3)
        self.assertEqual(Activity.objects.count(), 7)
        self.assertEqual(Registration.objects.count(), 13)
        self.assertSetEqual(set(Registration.objects.values_list("status", flat=True)), set(dict(Registration.STATUS_CHOICES)))
        self.assertSetEqual(set(Activity.objects.values_list("status", flat=True)), set(dict(Activity.STATUS_CHOICES)))
        for user in User.objects.all():
            self.assertTrue(user.check_password(DEMO_PASSWORD))
        participant = User.objects.get(username="demo_ana")
        organizer = User.objects.get(username="demo_organizador")
        self.assertFalse(participant.is_staff)
        self.assertFalse(participant.is_superuser)
        self.assertTrue(organizer.is_staff)
        self.assertFalse(organizer.is_superuser)
        self.assertTrue(organizer.has_perm("activities.add_activity"))
        self.assertFalse(organizer.has_perm("accounts.change_user"))
        self.assertTrue(User.objects.get(username="demo_admin").is_superuser)
        for activity in Activity.objects.all():
            activity.full_clean()
            self.assertLess(activity.confirmation_deadline, activity.starts_at)
            if activity.status != "FINISHED":
                self.assertGreater(activity.starts_at, timezone.now())
            self.assertLessEqual(occupied_seats(activity.registrations).count(), activity.max_participants)
        self.assertTrue(Registration.objects.filter(status="WAITLIST", seat_offered_at__isnull=False).exists())
        self.assertTrue(Registration.objects.filter(status="WAITLIST", seat_offered_at__isnull=True).exists())

    def test_second_run_is_a_complete_no_op_even_with_different_password(self):
        self.seed()
        snapshot = self.snapshot()
        self.seed(password="OutraSenha!987")
        self.assertEqual(self.snapshot(), snapshot)

    def test_preserves_existing_data_and_shared_permissions(self):
        user = User.objects.create_user(username="pessoa_existente", password="SenhaOriginal!987")
        modality = Modality.objects.create(name="Futebol real")
        location = Location.objects.create(name="Quadra real", city="Lavras", state="MG")
        start = timezone.now() + timedelta(days=5)
        activity = Activity.objects.create(title="Atividade real", organizer=user, modality=modality, location=location,
                                          starts_at=start, ends_at=start + timedelta(hours=1), confirmation_deadline=start - timedelta(days=1), max_participants=3)
        Registration.objects.create(activity=activity, participant=user, status="WAITLIST")
        group = Group.objects.get(name="Organizador")
        group.permissions.clear()
        group.permissions.add(Permission.objects.get(codename="add_user"))
        snapshot = self.snapshot()
        self.seed()
        self.assert_preserved(snapshot)

    def test_preserves_changes_to_existing_demo_records(self):
        self.seed()
        User.objects.filter(username="demo_ana").update(first_name="Nome editado", is_active=False)
        activity = Activity.objects.get(title="[DEMO] Corrida com aprovação")
        Activity.objects.filter(pk=activity.pk).update(status="CANCELED", starts_at=activity.starts_at + timedelta(minutes=1))
        Registration.objects.filter(activity=activity, status="PENDING").update(status="REJECTED", organizer_notes="Nota editada")
        snapshot = self.snapshot()
        self.seed()
        self.assertEqual(self.snapshot(), snapshot)

    def test_conflicting_username_aborts_without_changes(self):
        User.objects.create_user(username="demo_organizador", email="pessoa@example.com", password="MinhaSenha!987")
        snapshot = self.snapshot()
        with self.assertRaisesMessage(CommandError, "Nenhum dado foi alterado"):
            self.seed()
        self.assertEqual(self.snapshot(), snapshot)
