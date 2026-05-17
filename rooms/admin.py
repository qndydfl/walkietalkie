from django.contrib import admin
from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "owner",
        "is_private",
        "has_password_display",
        "member_count",
        "message_count",
        "created_at",
    ]

    list_filter = [
        "is_private",
        "created_at",
    ]

    search_fields = [
        "title",
        "description",
        "owner__username",
        "owner__nickname",
    ]

    filter_horizontal = ["members"]

    readonly_fields = [
        "created_at",
        "member_count",
        "message_count",
    ]

    ordering = ["-created_at"]

    def has_password_display(self, obj):
        return bool(obj.password)

    has_password_display.boolean = True
    has_password_display.short_description = "비밀번호"

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "멤버 수"

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = "메시지 수"