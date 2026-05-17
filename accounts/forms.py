from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "name", "nickname", "password1", "password2"]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "nickname", "profile_image"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "nickname": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "profile_image": forms.ClearableFileInput(attrs={
                "class": "form-control",
            }),
        }