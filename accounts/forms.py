import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from universities.models import COUNTRIES, University


class BootstrapFormMixin:
    """Apply consistent Bootstrap 5 classes to all rendered widgets."""

    def _style_fields(self):
        for name, field in self.fields.items():
            widget = field.widget
            css = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{css} form-check-input".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = f"{css} form-select".strip()
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = f"{css} form-control".strip()
                widget.attrs.setdefault("rows", 4)
            else:
                widget.attrs["class"] = f"{css} form-control".strip()
            if name in self.errors:
                widget.attrs["class"] += " is-invalid"


class RepresentativeRegistrationForm(BootstrapFormMixin, UserCreationForm):
    """Creates a representative account and the linked university in one step."""

    first_name = forms.CharField(max_length=150, label="First name")
    last_name = forms.CharField(max_length=150, label="Last name")
    email = forms.EmailField(label="Institutional email")
    job_title = forms.CharField(max_length=120, required=False, label="Job title")
    phone = forms.CharField(max_length=40, required=False, label="Phone (optional)")

    university_name = forms.CharField(max_length=200, label="University name")
    country = forms.ChoiceField(choices=[(c, c) for c in COUNTRIES], label="Country")
    city = forms.CharField(max_length=120, label="City / location")
    website = forms.URLField(
        max_length=300,
        required=False,
        label="University website",
        assume_scheme="https",
    )
    description = forms.CharField(
        label="Institutional description",
        widget=forms.Textarea,
        min_length=40,
        help_text="At least 40 characters describing your institution and its AI context.",
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "job_title",
            "phone",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = (
            "Letters, digits and @/./+/-/_ only. Used to sign in."
        )
        self.fields["password1"].help_text = "At least 8 characters."
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_university_name(self):
        name = self.cleaned_data["university_name"].strip()
        if University.objects.filter(name__iexact=name).exists():
            raise ValidationError("This university is already registered on GUCAIR.")
        return name

    def clean_website(self):
        website = self.cleaned_data.get("website", "").strip()
        if website and not re.match(r"^https?://", website, re.IGNORECASE):
            website = f"https://{website}"
        return website

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = user.profile
            profile.job_title = self.cleaned_data.get("job_title", "")
            profile.phone = self.cleaned_data.get("phone", "")
            profile.save()
            university = University.objects.create(
                name=self.cleaned_data["university_name"],
                country=self.cleaned_data["country"],
                city=self.cleaned_data["city"],
                website=self.cleaned_data.get("website", ""),
                description=self.cleaned_data["description"],
                created_by=user,
            )
            profile.university = university
            profile.save(update_fields=["university"])
        return user


class GUCAIRLoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Username", "autofocus": True}
        )
        self.fields["password"].widget.attrs["placeholder"] = "Password"
        self._style_fields()


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise ValidationError("Another account already uses this email address.")
        return email


class RepresentativeProfileForm(BootstrapFormMixin, forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        from accounts.models import UserProfile

        model = UserProfile
        fields = ["job_title", "phone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.instance.user.first_name
        self.fields["last_name"].initial = self.instance.user.last_name
        self.fields["email"].initial = self.instance.user.email
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.user_id)
            .exists()
        ):
            raise ValidationError("Another account already uses this email address.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile.save()
        return profile


class StyledPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
