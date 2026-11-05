from django import forms
from django.db import models


class ClockTimeInput(forms.TimeInput):
    input_type = "time"

    def __init__(self):
        super().__init__(format="%H:%M:%S", attrs={"step": "1", "aria-label": "Horário"})


class CalendarDateInput(forms.DateInput):
    input_type = "date"

    def __init__(self):
        super().__init__(format="%Y-%m-%d")


class ClockSplitDateTime(forms.SplitDateTimeWidget):
    template_name = "widgets/date_time.html"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
        # Sem DateTimeShortcuts: não sobrepõe o calendário do Django/Jazzmin.
        self.widgets = [CalendarDateInput(), ClockTimeInput()]


class ClockAdminMixin:
    formfield_overrides = {
        models.DateTimeField: {"widget": ClockSplitDateTime},
        models.TimeField: {"widget": ClockTimeInput},
    }
