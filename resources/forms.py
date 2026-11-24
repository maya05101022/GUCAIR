from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Resource


class ResourceForm(BootstrapFormMixin, forms.ModelForm):
    external_link = forms.URLField(
        max_length=400, required=False, assume_scheme="https"
    )

    class Meta:
        model = Resource
        fields = ["title", "category", "summary", "content", "external_link", "is_published"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content"].widget.attrs.update({"rows": 12})
        self.fields["summary"].widget.attrs.update({"rows": 3})
        self.fields["external_link"].required = False
        self._style_fields()

    def clean_external_link(self):
        link = self.cleaned_data.get("external_link", "").strip()
        if link and not link.lower().startswith(("http://", "https://")):
            link = f"https://{link}"
        return link
