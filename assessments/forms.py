from django import forms

from accounts.forms import BootstrapFormMixin

from .models import AssessmentQuestion
from .questions_data import RESPONSE_SCALE
from .services import get_active_questions


class AssessmentForm(BootstrapFormMixin, forms.Form):
    """Dynamically builds one required radio group per active question."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = get_active_questions()
        choices = [(value, label) for value, label, _ in RESPONSE_SCALE]
        for question in self.questions:
            self.fields[f"q_{question.pk}"] = forms.TypedChoiceField(
                label=question.text,
                choices=choices,
                coerce=int,
                required=True,
                error_messages={
                    "required": "Select a maturity level for this question.",
                    "invalid_choice": "Select one of the 0-4 maturity levels.",
                },
                widget=forms.RadioSelect(
                    attrs={"class": "readiness-radio", "data-question": question.pk}
                ),
            )

    def answers(self):
        return {
            question.pk: self.cleaned_data[f"q_{question.pk}"]
            for question in self.questions
        }

    def grouped_questions(self):
        from .models import DIMENSIONS

        groups = []
        for key, label, description in DIMENSIONS:
            items = [q for q in self.questions if q.dimension == key]
            if not items:
                continue
            groups.append(
                {
                    "key": key,
                    "label": label,
                    "description": description,
                    "questions": [
                        {"question": q, "field": self[f"q_{q.pk}"]} for q in items
                    ],
                }
            )
        return groups
