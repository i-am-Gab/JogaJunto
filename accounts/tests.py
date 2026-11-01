from django.contrib.auth.models import Group
from django.test import TestCase

from .models import GROUP_ORGANIZER, GROUP_PARTICIPANT, ROLE_ORGANIZER, User
from .permissions import ensure_access_groups, promote_to_organizer


class AccessGroupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ensure_access_groups()

    def test_groups_are_created_with_permissions(self):
        participant = Group.objects.get(name=GROUP_PARTICIPANT)
        organizer = Group.objects.get(name=GROUP_ORGANIZER)

        self.assertTrue(participant.permissions.filter(codename="view_activity").exists())
        self.assertFalse(participant.permissions.filter(codename="add_activity").exists())
        self.assertTrue(organizer.permissions.filter(codename="add_activity").exists())
        self.assertTrue(organizer.permissions.filter(codename="change_registration").exists())

    def test_new_user_is_staff_and_participant(self):
        user = User.objects.create_user(username="ana", password="senha123")
        user.refresh_from_db()

        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, "participante")
        self.assertTrue(user.groups.filter(name=GROUP_PARTICIPANT).exists())
        self.assertFalse(user.groups.filter(name=GROUP_ORGANIZER).exists())
        self.assertTrue(user.has_perm("activities.view_activity"))
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
