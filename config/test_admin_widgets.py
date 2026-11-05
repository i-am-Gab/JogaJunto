from datetime import datetime

from django import forms
from django.test import SimpleTestCase

from .admin_widgets import ClockSplitDateTime


class ClockWidgetTests(SimpleTestCase):
    def test_existing_time_and_seconds_are_preserved(self):
        widget = ClockSplitDateTime()
        html = widget.render("starts_at", datetime(2026, 11, 5, 14, 37, 25))
        self.assertIn('type="time"', html)
        self.assertIn('value="14:37:25"', html)
        self.assertNotIn('class="vTimeField"', html)
        field = forms.SplitDateTimeField(widget=widget)
        self.assertEqual(field.clean(["2026-11-05", "14:37:25"]).hour, 14)

    def test_optional_empty_time(self):
        field = forms.SplitDateTimeField(widget=ClockSplitDateTime(), required=False)
        self.assertIsNone(field.clean(["", ""]))
