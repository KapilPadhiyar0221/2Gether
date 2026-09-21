from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("", views.home, name="home"),
    path("explore/", views.explore, name="explore"),
    path("post/new/", views.create_post, name="create"),
    path("post/<int:pk>/", views.post_detail, name="detail"),
    path("post/<int:pk>/delete/", views.delete_post, name="delete"),
    path("post/<int:pk>/like/", views.toggle_like, name="like"),
    path("post/<int:pk>/comments/", views.post_comments, name="comments"),
    path("post/<int:pk>/comment/", views.add_comment, name="add_comment"),
    path("comment/<int:pk>/delete/", views.delete_comment, name="delete_comment"),
]
