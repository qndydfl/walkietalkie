from django.db import models
from django.conf import settings


class DirectRoom(models.Model):
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="direct_rooms"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DM Room {self.id}"


class DirectMessage(models.Model):
    room = models.ForeignKey(
        DirectRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_dm_messages"
    )
    content = models.TextField()
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="read_dm_messages",
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def read_count(self):
        return self.read_by.count()

    def __str__(self):
        return f"{self.sender} : {self.content[:30]}"