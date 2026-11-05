from django import forms
from .models import Activity
from config.admin_widgets import ClockSplitDateTime


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude = ["organizer", "status", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["modality"].empty_label = "Selecione uma modalidade"
        self.fields["location"].empty_label = "Selecione um local"
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

        for name in ("starts_at", "ends_at", "confirmation_deadline"):
            original = self.fields[name]
            self.fields[name] = forms.SplitDateTimeField(
                label=original.label, help_text=original.help_text,
                widget=ClockSplitDateTime(),
                error_messages={"invalid_date": "Informe uma data válida.", "invalid_time": "Informe um horário válido."},
            )
        self.fields["registration_type"].help_text = "Automática: a vaga é confirmada na inscrição. Mediante aprovação: você analisa a solicitação antes de confirmar a vaga."
