from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import Follow
from common.http import wants_json
from notifications.models import Notification

from .forms import CommentForm, PostForm
from .models import Comment, Like, Post

PAGE_SIZE = 8


def feed_queryset(user):
    """Posts with everything a card needs, in one round trip."""
    qs = (
        Post.objects.select_related("author", "author__profile")
        .annotate(like_total=Count("likes", distinct=True),
                  comment_total=Count("comments", distinct=True))
        # annotate() clears Meta.ordering to keep GROUP BY sane, and an
        # unordered queryset makes pagination repeat rows. Put it back.
        .order_by("-created_at", "-pk")
    )
    if user.is_authenticated:
        qs = qs.annotate(
            liked=Exists(Like.objects.filter(post=OuterRef("pk"), user=user))
        )
    return qs


def paginate_feed(request, queryset, template="partials/_feed_page.html", extra=None):
    page_number = request.GET.get("page") or 1
    paginator = Paginator(queryset, PAGE_SIZE)
    page = paginator.get_page(page_number)
    context = {"page_obj": page, "posts": page.object_list, **(extra or {})}
    if wants_json(request):
        return JsonResponse({
            "ok": True,
            "html": render_to_string(template, context, request=request),
            "has_next": page.has_next(),
            "next_page": page.next_page_number() if page.has_next() else None,
        })
    return None, context


@login_required
def home(request):
    """Posts from people you follow, plus your own."""
    following_ids = Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)
    qs = feed_queryset(request.user).filter(
        Q(author_id__in=following_ids) | Q(author=request.user)
    )
    following_anyone = following_ids.exists()

    json_response = paginate_feed(request, qs)
    if isinstance(json_response, JsonResponse):
        return json_response
    _, context = json_response

    context.update({
        "form": PostForm(),
        "following_anyone": following_anyone,
        "suggestions": suggested_people(request.user),
        "active_nav": "home",
    })
    return render(request, "posts/home.html", context)


@login_required
def explore(request):
    """Everything, newest first — how you find people to follow."""
    qs = feed_queryset(request.user).exclude(author=request.user)
    json_response = paginate_feed(request, qs)
    if isinstance(json_response, JsonResponse):
        return json_response
    _, context = json_response
    context.update({
        "suggestions": suggested_people(request.user),
        "active_nav": "explore",
    })
    return render(request, "posts/explore.html", context)


def suggested_people(user, limit=4):
    """People you don't follow yet, busiest first."""
    already = list(Follow.objects.filter(follower=user).values_list("following_id", flat=True))
    return (
        User.objects.exclude(id__in=already + [user.id])
        .select_related("profile")
        .annotate(followers_total=Count("followers", distinct=True),
                  posts_total=Count("posts", distinct=True))
        .order_by("-followers_total", "-posts_total")[:limit]
    )


@login_required
def post_detail(request, pk):
    post = get_object_or_404(feed_queryset(request.user), pk=pk)
    comments = post.comments.select_related("author", "author__profile")
    return render(request, "posts/detail.html", {
        "post": post,
        "comments": comments,
        "comment_form": CommentForm(),
        "active_nav": "",
    })


@login_required
@require_POST
def create_post(request):
    form = PostForm(request.POST, request.FILES)
    if not form.is_valid():
        errors = " ".join(e for field in form.errors.values() for e in field)
        if wants_json(request):
            return JsonResponse({"ok": False, "error": errors}, status=400)
        messages.error(request, errors)
        return redirect("posts:home")

    post = form.save(commit=False)
    post.author = request.user
    dimensions = getattr(form, "_dimensions", None)
    if dimensions:
        post.image_width, post.image_height = dimensions
    post.save()

    post = feed_queryset(request.user).get(pk=post.pk)
    if wants_json(request):
        return JsonResponse({
            "ok": True,
            "html": render_to_string("partials/_post.html", {"post": post}, request=request),
        })
    messages.success(request, "Posted.")
    return redirect("posts:home")


@login_required
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author_id != request.user.id:
        return JsonResponse({"ok": False, "error": "This isn't your post."}, status=403)
    if post.image:
        post.image.delete(save=False)
    post.delete()
    if wants_json(request):
        return JsonResponse({"ok": True, "id": pk})
    messages.success(request, "Post deleted.")
    return redirect("posts:home")


@login_required
@require_POST
def toggle_like(request, pk):
    post = get_object_or_404(Post.objects.select_related("author"), pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if created:
        Notification.push(post.author, request.user, Notification.Verb.LIKE, post=post)
    else:
        like.delete()
        post.notifications.filter(actor=request.user, verb=Notification.Verb.LIKE).delete()
    return JsonResponse({
        "ok": True, "liked": created, "count": post.likes.count(), "id": post.pk
    })


@login_required
def post_comments(request, pk):
    """Comment thread, rendered server-side so markup stays in one place."""
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.select_related("author", "author__profile")
    html = render_to_string(
        "partials/_comment_list.html", {"post": post, "comments": comments}, request=request
    )
    return JsonResponse({"ok": True, "html": html, "count": comments.count()})


@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(Post.objects.select_related("author"), pk=pk)
    form = CommentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "error": "Write something first."}, status=400)

    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    Notification.push(post.author, request.user, Notification.Verb.COMMENT,
                      post=post, comment=comment)
    return JsonResponse({
        "ok": True,
        "count": post.comments.count(),
        "html": render_to_string(
            "partials/_comment.html", {"comment": comment, "post": post}, request=request
        ),
    })


@login_required
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment.objects.select_related("post", "author"), pk=pk)
    if not comment.can_delete(request.user):
        return JsonResponse({"ok": False, "error": "You can't delete this comment."}, status=403)
    post_id = comment.post_id
    comment.delete()
    return JsonResponse({
        "ok": True, "id": pk, "count": Comment.objects.filter(post_id=post_id).count()
    })
