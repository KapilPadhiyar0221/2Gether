from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("join/", views.signup, name="signup"),
    path("signin/", views.SignInView.as_view(), name="login"),
    path("signout/", views.sign_out, name="logout"),
    path("search/", views.search, name="search"),
    path("settings/profile/", views.edit_profile, name="edit_profile"),
    path("@<str:username>/", views.profile, name="profile"),
    path("@<str:username>/followers/", views.follow_list, {"mode": "followers"}, name="followers"),
    path("@<str:username>/following/", views.follow_list, {"mode": "following"}, name="following"),
    path("@<str:username>/follow/", views.toggle_follow, name="follow"),
]
