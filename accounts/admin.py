from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        "id",
        "profile_preview",
        "username",
        "name",
        "nickname",
        "email",
        "is_staff",
        "is_active",
        "date_joined",
    ]

    list_filter = [
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
    ]

    search_fields = [
        "username",
        "name",
        "nickname",
        "email",
    ]

    ordering = ["-date_joined"]

    fieldsets = UserAdmin.fieldsets + (
        ("추가 프로필 정보", {
            "fields": (
                "name",
                "nickname",
                "profile_image",
                "profile_preview",
            )
        }),
    )

    readonly_fields = ["profile_preview"]

    def profile_preview(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" style="width:45px;height:45px;border-radius:50%;object-fit:cover;" />',
                obj.profile_image.url
            )

        return "이미지 없음"

    profile_preview.short_description = "프로필"