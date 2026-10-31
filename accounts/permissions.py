from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from .models import (
    GROUP_ORGANIZER,
    GROUP_PARTICIPANT,
    ROLE_ORGANIZER,
    ROLE_PARTICIPANT,
)

PARTICIPANT_PERMISSIONS = (
    ("accounts", "view_user"),
    ("accounts", "change_user"),
    ("activities", "view_activity"),
    ("activities", "view_modality"),
    ("activities", "view_location"),
    ("registrations", "view_registration"),
    ("registrations", "view_payment"),
    ("registrations", "view_attendance"),
)

ORGANIZER_PERMISSIONS = PARTICIPANT_PERMISSIONS + (
    ("activities", "add_activity"),
    ("activities", "change_activity"),
    ("activities", "delete_activity"),
    ("activities", "add_modality"),
    ("activities", "change_modality"),
    ("activities", "add_location"),
    ("activities", "change_location"),
    ("registrations", "add_registration"),
    ("registrations", "change_registration"),
    ("registrations", "add_payment"),
    ("registrations", "change_payment"),
    ("registrations", "add_attendance"),
    ("registrations", "change_attendance"),
)


def _get_permissions(pairs):
    permissions = []
    for app_label, codename in pairs:
        permission = Permission.objects.filter(
            content_type__app_label=app_label, codename=codename
        ).first()
        if permission:
            permissions.append(permission)
    return permissions


def ensure_access_groups():
    participant, _ = Group.objects.get_or_create(name=GROUP_PARTICIPANT)
    participant.permissions.set(_get_permissions(PARTICIPANT_PERMISSIONS))

    organizer, _ = Group.objects.get_or_create(name=GROUP_ORGANIZER)
    organizer.permissions.set(_get_permissions(ORGANIZER_PERMISSIONS))

    return participant, organizer


def sync_user_group(user):
    if user.is_superuser:
        return user

    participant, organizer = ensure_access_groups()
    role = user.role or ROLE_PARTICIPANT

    if role == ROLE_ORGANIZER:
        user.groups.add(organizer)
        user.groups.remove(participant)
    else:
        user.groups.add(participant)
        user.groups.remove(organizer)

    return user


def promote_to_organizer(user):
    if user.is_superuser:
        return user

    if user.role != ROLE_ORGANIZER:
        get_user_model().objects.filter(pk=user.pk).update(role=ROLE_ORGANIZER)
        user.role = ROLE_ORGANIZER

    sync_user_group(user)
    user.refresh_from_db()
    for cache_attr in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
        if hasattr(user, cache_attr):
            delattr(user, cache_attr)
    return user
