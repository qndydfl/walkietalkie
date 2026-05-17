from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password


class Room(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_rooms"
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="joined_rooms",
        blank=True
    )

    is_private = models.BooleanField(default=False)
    password = models.CharField(max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        if raw_password:
            self.password = make_password(raw_password)
        else:
            self.password = ""

    def check_password(self, raw_password):
        if not self.password:
            return True
        return check_password(raw_password, self.password)

    def has_password(self):
        return bool(self.password)

    def can_enter(self, user):
        if not self.is_private:
            return True

        if self.owner == user:
            return True

        return self.members.filter(id=user.id).exists()

    def __str__(self):
        return self.title