from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse


def post_image_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"posts/{instance.author_id}/{instance.created_at:%Y%m}/{filename[:40]}.{ext}"


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    body = models.TextField(max_length=1000, blank=True)
    image = models.ImageField(upload_to="posts/%Y/%m/", blank=True, null=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"]), models.Index(fields=["author", "-created_at"])]
        constraints = [
            # A post has to carry something.
            models.CheckConstraint(
                condition=~Q(body="") | ~Q(image=""),
                name="post_not_empty",
            )
        ]

    def __str__(self):
        return f"{self.author}: {self.body[:40]}"

    def get_absolute_url(self):
        return reverse("posts:detail", args=[self.pk])

    # Wider than this and the image gets letterboxed; taller and it dominates
    # the feed. Both ends are clamped so every card reserves a sane frame.
    MIN_RATIO = 0.8    # 4:5 portrait
    MAX_RATIO = 1.91   # wide landscape

    @property
    def aspect_ratio(self):
        """Reserves the right space before the image loads, so the feed never jumps."""
        if not (self.image_width and self.image_height):
            return None
        ratio = self.image_width / self.image_height
        return round(min(max(ratio, self.MIN_RATIO), self.MAX_RATIO), 4)

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_like_per_user")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} likes #{self.post_id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["post", "created_at"])]

    def __str__(self):
        return f"{self.author} on #{self.post_id}"

    def can_delete(self, user):
        """Comment authors delete their own; post authors moderate their thread."""
        return user.is_authenticated and (
            self.author_id == user.id or self.post.author_id == user.id
        )
