from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("count/", views.unread_count, name="count"),
    path("read/", views.mark_all_read, name="mark_read"),
]
