from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.db import models


class ClockTimeInput(forms.TimeInput):
    input_type = "time"

    def __init__(self):
        super().__init__(format="%H:%M:%S", attrs={"step": "1", "aria-label": "Horário"})


class ClockSplitDateTime(AdminSplitDateTime):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        # Mantém o calendário do admin e usa o relógio nativo do navegador.
        self.widgets[1] = ClockTimeInput()


class ClockAdminMixin:
    formfield_overrides = {
        models.DateTimeField: {"widget": ClockSplitDateTime},
        models.TimeField: {"widget": ClockTimeInput},
    }
