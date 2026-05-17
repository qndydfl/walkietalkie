from django import forms
from .models import Room
from django.contrib.auth import get_user_model


User = get_user_model()

class RoomForm(forms.ModelForm):
    raw_password = forms.CharField(
        label="방 비밀번호",
        required=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "비밀번호 없이 만들려면 비워두세요",
        })
    )

    class Meta:
        model = Room
        fields = ["title", "description", "is_private", "raw_password"]

        labels = {
            "title": "방 제목",
            "description": "방 설명",
            "is_private": "비공개 방으로 만들기",
        }

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "방 제목",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "방 설명",
            }),
            "is_private": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def save(self, commit=True):
        room = super().save(commit=False)
        room.set_password(self.cleaned_data.get("raw_password"))

        if commit:
            room.save()

        return room


class RoomPasswordForm(forms.Form):
    password = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "방 비밀번호를 입력하세요",
        })
    )


class InviteUserForm(forms.Form):
    keyword = forms.CharField(
        label="초대할 사용자",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "닉네임 또는 아이디를 입력하세요",
        })
    )