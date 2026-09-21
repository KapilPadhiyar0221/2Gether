from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import IntegrityError
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from notifications.models import Notification
from common.http import wants_json
from posts.views import feed_queryset, paginate_feed

from .forms import LoginForm, ProfileForm, SignUpForm
from .models import Follow


def people_queryset(viewer):
    """Users with follower/post counts and the viewer's follow state attached."""
    qs = User.objects.select_related("profile").annotate(
        followers_total=Count("followers", distinct=True),
        posts_total=Count("posts", distinct=True),
    )
    if viewer.is_authenticated:
        qs = qs.annotate(
            is_followed=Exists(
                Follow.objects.filter(follower=viewer, following=OuterRef("pk"))
            )
        )
    return qs


def signup(request):
    if request.user.is_authenticated:
        return redirect("posts:home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome to 2gether, {user.username}.")
        return redirect("posts:explore")
    return render(request, "accounts/signup.html", {"form": form})


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@require_POST
def sign_out(request):
    logout(request)
    messages.success(request, "Signed out.")
    return redirect("accounts:login")


@login_required
def profile(request, username):
    person = get_object_or_404(people_queryset(request.user), username__iexact=username)
    posts = feed_queryset(request.user).filter(author=person)

    json_response = paginate_feed(request, posts)
    if isinstance(json_response, JsonResponse):
        return json_response
    _, context = json_response

    context.update({
        "person": person,
        "profile": person.profile,
        "is_self": person.id == request.user.id,
        "is_followed": getattr(person, "is_followed", False),
        "active_nav": "profile" if person.id == request.user.id else "",
    })
    return render(request, "accounts/profile.html", context)


@login_required
def edit_profile(request):
    form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user.profile
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile saved.")
        return redirect("accounts:profile", username=request.user.username)
    return render(request, "accounts/edit_profile.html", {"form": form, "active_nav": "profile"})


@login_required
def follow_list(request, username, mode):
    person = get_object_or_404(User.objects.select_related("profile"), username__iexact=username)
    if mode == "followers":
        ids = Follow.objects.filter(following=person).values_list("follower_id", flat=True)
        heading = "Followers"
        blank = f"No one follows @{person.username} yet."
    else:
        ids = Follow.objects.filter(follower=person).values_list("following_id", flat=True)
        heading = "Following"
        blank = f"@{person.username} isn't following anyone yet."
    people = people_queryset(request.user).filter(id__in=list(ids))
    return render(request, "accounts/people.html", {
        "person": person, "people": people, "heading": heading,
        "blank_message": blank, "mode": mode, "active_nav": "",
    })


@login_required
@require_POST
def toggle_follow(request, username):
    target = get_object_or_404(User.objects.select_related("profile"), username__iexact=username)
    if target.id == request.user.id:
        return JsonResponse({"ok": False, "error": "You can't follow yourself."}, status=400)

    existing = Follow.objects.filter(follower=request.user, following=target)
    if existing.exists():
        existing.delete()
        Notification.objects.filter(
            recipient=target, actor=request.user, verb=Notification.Verb.FOLLOW
        ).delete()
        following = False
    else:
        try:
            Follow.objects.create(follower=request.user, following=target)
        except IntegrityError:
            return JsonResponse({"ok": False, "error": "Couldn't update that."}, status=400)
        Notification.push(target, request.user, Notification.Verb.FOLLOW)
        following = True

    return JsonResponse({
        "ok": True,
        "following": following,
        "username": target.username,
        "followers": target.followers.count(),
    })


@login_required
def search(request):
    query = (request.GET.get("q") or "").strip()
    results = []
    if query:
        results = people_queryset(request.user).filter(
            Q(username__icontains=query)
            | Q(profile__display_name__icontains=query)
            | Q(profile__bio__icontains=query)
        ).order_by("-followers_total")[:20]

    if wants_json(request):
        return JsonResponse({
            "ok": True,
            "count": len(results),
            "query": query,
            "html": render_to_string(
                "partials/_search_results.html", {"results": results, "query": query},
                request=request,
            ),
        })
    return render(request, "accounts/search.html", {
        "results": results, "query": query, "active_nav": "search",
    })
