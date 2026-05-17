from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "room",
        "sender",
        "receiver",
        "short_content",
        "is_private",
        "read_user_count",
        "created_at",
    ]

    list_filter = [
        "room",
        "is_private",
        "created_at",
    ]

    search_fields = [
        "content",
        "sender__username",
        "sender__nickname",
        "receiver__username",
        "receiver__nickname",
        "room__title",
    ]

    readonly_fields = [
        "created_at",
        "read_user_count",
    ]

    filter_horizontal = ["read_by"]

    ordering = ["-created_at"]

    def short_content(self, obj):
        if len(obj.content) > 30:
            return obj.content[:30] + "..."
        return obj.content

    short_content.short_description = "내용"

    def read_user_count(self, obj):
        return obj.read_by.count()

    read_user_count.short_description = "읽은 사람 수"