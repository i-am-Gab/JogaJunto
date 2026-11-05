from django.db import migrations


def seed_current_status(apps, schema_editor):
    Registration = apps.get_model("registrations", "Registration")
    Notification = apps.get_model("registrations", "Notification")
    database = schema_editor.connection.alias
    labels = {
        "PENDING": "pendente de aprovação", "APPROVED": "aprovada",
        "REJECTED": "rejeitada", "WAITLIST": "na lista de espera", "CANCELED": "cancelada",
    }
    for registration in Registration.objects.using(database).select_related("activity", "participant").iterator():
        if Notification.objects.using(database).filter(registration_id=registration.pk).exists():
            continue
        Notification.objects.using(database).create(
            recipient_id=registration.participant_id, registration_id=registration.pk,
            message=f'Situação atual da sua inscrição em "{registration.activity.title}": {labels[registration.status]}.',
        )
        if registration.status == "PENDING":
            Notification.objects.using(database).create(
                recipient_id=registration.activity.organizer_id, registration_id=registration.pk,
                message=f'A inscrição de {registration.participant.username} em "{registration.activity.title}" está pendente de sua aprovação.',
            )


class Migration(migrations.Migration):
    dependencies = [("registrations", "0003_alter_attendance_check_in_at_and_more")]
    operations = [migrations.RunPython(seed_current_status, migrations.RunPython.noop)]
