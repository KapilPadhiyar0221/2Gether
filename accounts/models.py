from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.urls import reverse
from django.utils.text import slugify


def avatar_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"avatars/{instance.user_id}/{slugify(instance.user.username)}.{ext}"


class Profile(models.Model):
    """Everything about a person that isn't authentication."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    display_name = models.CharField(max_length=50, blank=True)
    bio = models.CharField(max_length=180, blank=True)
    location = models.CharField(max_length=60, blank=True)
    website = models.URLField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to=avatar_path, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse("accounts:profile", args=[self.user.username])

    @property
    def name(self):
        return self.display_name or self.user.username

    @property
    def initials(self):
        source = (self.display_name or self.user.username).strip()
        parts = [p for p in source.split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return source[:2].upper() if source else "?"

    # Counts are read constantly in templates, so keep them on one hop.
    @property
    def follower_count(self):
        return self.user.followers.count()

    @property
    def following_count(self):
        return self.user.following.count()

    @property
    def post_count(self):
        return self.user.posts.count()


class Follow(models.Model):
    """A directed edge: `follower` follows `following`."""

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="unique_follow_edge"
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("following")), name="no_self_follow"
            ),
        ]
        indexes = [models.Index(fields=["following", "-created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower} -> {self.following}"
