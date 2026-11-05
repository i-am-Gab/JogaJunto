from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from .models import (
    GROUP_ORGANIZER,
    GROUP_PARTICIPANT,
    ROLE_ORGANIZER,
    ROLE_PARTICIPANT,
)

# Participantes usam apenas as telas públicas, sem permissões administrativas.
PARTICIPANT_PERMISSIONS = ()

ORGANIZER_PERMISSIONS = (
    ("activities", "view_activity"),
    ("activities", "add_activity"),
    ("activities", "change_activity"),
    ("activities", "delete_activity"),
    ("activities", "view_modality"),
    ("activities", "add_modality"),
    ("activities", "view_location"),
    ("activities", "add_location"),
    ("registrations", "view_registration"),
    ("registrations", "add_registration"),
    ("registrations", "change_registration"),
    ("registrations", "view_payment"),
    ("registrations", "add_payment"),
    ("registrations", "change_payment"),
    ("registrations", "view_attendance"),
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

    is_staff = role == ROLE_ORGANIZER
    get_user_model().objects.filter(pk=user.pk).update(is_staff=is_staff)
    user.is_staff = is_staff
    user.groups.set([organizer if is_staff else participant])
    user.user_permissions.clear()
    for attr in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
        user.__dict__.pop(attr, None)

    return user


def promote_to_organizer(user):
    if user.is_superuser:
        return user

    User = get_user_model()
    
    # Atualiza a flag de equipe para acesso ao painel Admin
    if not user.is_staff or user.role != ROLE_ORGANIZER:
        User.objects.filter(pk=user.pk).update(role=ROLE_ORGANIZER, is_staff=True)
        user.role = ROLE_ORGANIZER
        user.is_staff = True

    sync_user_group(user)
    user.refresh_from_db()
    
    # Limpa cache de permissões da sessão atual
    for cache_attr in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
        if hasattr(user, cache_attr):
            delattr(user, cache_attr)
            
    return user
