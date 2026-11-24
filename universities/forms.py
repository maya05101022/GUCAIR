from django import forms

from accounts.forms import BootstrapFormMixin

from .models import COUNTRIES, University


class UniversityForm(BootstrapFormMixin, forms.ModelForm):
    country = forms.ChoiceField(choices=[(c, c) for c in COUNTRIES])
    website = forms.URLField(
        max_length=300, required=False, assume_scheme="https"
    )

    class Meta:
        model = University
        fields = ["name", "country", "city", "website", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].widget.attrs.update({"rows": 6})
        self.fields["website"].required = False
        self._style_fields()

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = University.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A university with this name already exists.")
        return name

    def clean_website(self):
        website = self.cleaned_data.get("website", "").strip()
        if website and not website.lower().startswith(("http://", "https://")):
            website = f"https://{website}"
        return website


class UniversityAdminForm(UniversityForm):
    class Meta(UniversityForm.Meta):
        fields = [
            "name",
            "country",
            "city",
            "website",
            "description",
            "status",
            "review_note",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["review_note"].widget.attrs.update({"rows": 3})
        self._style_fields()
