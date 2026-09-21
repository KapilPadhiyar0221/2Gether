from django.contrib import admin

from .models import Comment, Like, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "short_body", "created_at")
    list_filter = ("created_at",)
    search_fields = ("body", "author__username")

    @admin.display(description="body")
    def short_body(self, obj):
        return obj.body[:60] or "(image only)"


admin.site.register(Like)
admin.site.register(Comment)
