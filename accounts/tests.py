from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import GROUP_ORGANIZER, GROUP_PARTICIPANT, ROLE_ORGANIZER, User
from .permissions import ensure_access_groups, promote_to_organizer


class SignupTests(TestCase):
    def test_public_signup_creates_participant_and_logs_in(self):
        response = self.client.post(reverse("signup"), {
            "username": "nova_pessoa", "email": "pessoa@example.com",
            "password1": "UmaSenha-Forte!987", "password2": "UmaSenha-Forte!987",
            "is_superuser": "true", "role": "organizador",
        })
        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(username="nova_pessoa")
        self.assertTrue(user.check_password("UmaSenha-Forte!987"))
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, GROUP_PARTICIPANT.lower())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_invalid_password_does_not_create_account(self):
        response = self.client.post(reverse("signup"), {
            "username": "nova_pessoa", "email": "pessoa@example.com",
            "password1": "UmaSenha-Forte!987", "password2": "outra",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="nova_pessoa").exists())

    def test_public_pages_link_to_signup(self):
        for name in ("home", "login"):
            self.assertContains(self.client.get(reverse(name)), reverse("signup"))


class AccessGroupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_access_groups()

    def test_groups_are_created_with_permissions(self):
        participant = Group.objects.get(name=GROUP_PARTICIPANT)
        organizer = Group.objects.get(name=GROUP_ORGANIZER)

        self.assertFalse(participant.permissions.exists())
        self.assertFalse(participant.permissions.filter(codename="add_activity").exists())
        self.assertTrue(organizer.permissions.filter(codename="add_activity").exists())
        self.assertTrue(organizer.permissions.filter(codename="change_registration").exists())

    def test_new_user_is_not_staff_and_is_participant(self):
        user = User.objects.create_user(username="ana", password="senha123")
        user.refresh_from_db()

        self.assertFalse(user.is_staff)
        self.assertEqual(user.role, "participante")
        self.assertTrue(user.groups.filter(name=GROUP_PARTICIPANT).exists())
        self.assertFalse(user.groups.filter(name=GROUP_ORGANIZER).exists())
        self.assertFalse(user.has_perm("activities.view_activity"))
        self.assertFalse(user.has_perm("activities.change_activity"))

    def test_promote_to_organizer_updates_role_and_group(self):
        user = User.objects.create_user(username="bruno", password="senha123")

        promote_to_organizer(user)
        user.refresh_from_db()

        self.assertEqual(user.role, ROLE_ORGANIZER)
        self.assertTrue(user.groups.filter(name=GROUP_ORGANIZER).exists())
        self.assertFalse(user.groups.filter(name=GROUP_PARTICIPANT).exists())
        self.assertTrue(user.has_perm("activities.add_activity"))
        self.assertTrue(user.has_perm("activities.change_activity"))


class RoleBoundaryTests(TestCase):
    def test_participant_cannot_enter_admin_even_with_legacy_staff_flag(self):
        user = User.objects.create_user(username="legacy", password="senha123")
        User.objects.filter(pk=user.pk).update(is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 302)
        self.assertNotContains(self.client.get(reverse("home")), "Painel Admin")
        self.assertEqual(self.client.get(reverse("create_activity")).status_code, 403)
        self.assertEqual(self.client.post(reverse("create_activity"), {}).status_code, 403)

    def test_role_change_updates_staff_and_permissions(self):
        user = User.objects.create_user(username="troca", role=ROLE_ORGANIZER)
        self.assertTrue(user.is_staff)
        user.role = "participante"
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.has_perm("activities.add_activity"))

    def test_organizer_cannot_manage_users_or_permissions(self):
        user = User.objects.create_user(username="org", role=ROLE_ORGANIZER)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:accounts_user_changelist")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:accounts_user_change", args=[user.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_group_changelist")).status_code, 403)

    def test_superuser_has_full_access(self):
        user = User.objects.create_superuser(username="root", password="senha123")
        self.client.force_login(user)
        for name in ("admin:index", "admin:accounts_user_changelist", "admin:auth_group_changelist"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_sync_access_repairs_existing_users(self):
        from django.core.management import call_command
        user = User.objects.create_user(username="antigo")
        User.objects.filter(pk=user.pk).update(is_staff=True)
        call_command("sync_access")
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
