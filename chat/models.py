from django.db import models
from django.conf import settings
from rooms.models import Room


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="received_messages"
    )
    content = models.TextField()
    is_private = models.BooleanField(default=False)

    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="read_messages",
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def read_count(self):
        return self.read_by.count()

    def is_read_by(self, user):
        return self.read_by.filter(id=user.id).exists()

    def __str__(self):
        return f"{self.sender} : {self.content[:30]}"