from django import forms

from accounts.forms import BootstrapFormMixin

from .models import ContactMessage


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "organization", "subject", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget.attrs.update({"rows": 6})
        self._style_fields()
