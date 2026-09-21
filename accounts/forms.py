from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from common.images import downscale, validate_image

from .models import Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
    )

    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(
                attrs={"autocomplete": "username", "placeholder": "pick a handle", "autofocus": True}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "at least 8 characters"}
        )
        self.fields["password2"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "type it once more"}
        )
        self.fields["username"].help_text = "Letters, digits and . _ - only."

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That handle is taken. Try another.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already uses this email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "placeholder": "handle", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password", "placeholder": "password"}
        )

    error_messages = {
        "invalid_login": "That handle and password don't match. Check both and try again.",
        "inactive": "This account is switched off.",
    }


class ProfileForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False, label="Remove current photo")

    class Meta:
        model = Profile
        fields = ("display_name", "bio", "location", "website", "avatar")
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "How your name appears"}),
            "bio": forms.Textarea(
                attrs={"rows": 3, "placeholder": "A line or two about you", "maxlength": 180}
            ),
            "location": forms.TextInput(attrs={"placeholder": "City, country"}),
            "website": forms.URLInput(attrs={"placeholder": "https://"}),
            "avatar": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {"display_name": "Name", "bio": "Bio", "avatar": "Profile photo"}

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar and hasattr(avatar, "file") and hasattr(avatar, "content_type"):
            validate_image(avatar)
            processed, _, _ = downscale(avatar, max_edge=512, quality=86)
            return processed
        return avatar

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.cleaned_data.get("remove_avatar"):
            profile.avatar.delete(save=False)
            profile.avatar = None
        if commit:
            profile.save()
        return profile
