from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Verb(models.TextChoices):
        LIKE = "like", "liked your post"
        COMMENT = "comment", "commented on your post"
        FOLLOW = "follow", "started following you"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="actions"
    )
    verb = models.CharField(max_length=16, choices=Verb.choices)
    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, null=True, blank=True,
        related_name="notifications",
    )
    comment = models.ForeignKey(
        "posts.Comment", on_delete=models.CASCADE, null=True, blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read", "-created_at"])]

    def __str__(self):
        return f"{self.actor} {self.get_verb_display()} -> {self.recipient}"

    @staticmethod
    def push(recipient, actor, verb, post=None, comment=None):
        """Create a notification, skipping self-directed noise."""
        if recipient == actor:
            return None
        return Notification.objects.create(
            recipient=recipient, actor=actor, verb=verb, post=post, comment=comment
        )
