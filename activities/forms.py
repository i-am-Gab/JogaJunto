from django import forms
from .models import Activity


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ["organizer", "status", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona a classe do Bootstrap em todos os campos automaticamente
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = (
                    "form-select"
                    if isinstance(field.widget, forms.Select)
                    else "form-control"
                )

        # Transforma os campos de data no calendário nativo do navegador
        self.fields["starts_at"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        )
        self.fields["ends_at"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        )
        self.fields["confirmation_deadline"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        )
