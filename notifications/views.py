from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from common.http import wants_json

from .models import Notification


def notifications_for(user, limit=None):
    qs = (
        user.notifications.select_related("actor", "actor__profile", "post", "comment")
        .all()
    )
    return qs[:limit] if limit else qs


@login_required
def inbox(request):
    items = notifications_for(request.user)
    unread = [n for n in items if not n.is_read]
    if wants_json(request):
        return JsonResponse({
            "ok": True,
            "unread": len(unread),
            "html": render_to_string(
                "partials/_notification_list.html", {"notifications": items[:20]}, request=request
            ),
        })
    return render(request, "notifications/inbox.html", {
        "notifications": items, "active_nav": "notifications",
    })


@login_required
def unread_count(request):
    return JsonResponse({
        "ok": True, "count": request.user.notifications.filter(is_read=False).count()
    })


@login_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({"ok": True, "count": 0})
