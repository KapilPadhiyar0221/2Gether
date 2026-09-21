def unread_notifications(request):
    """Badge count for the nav, on every page."""
    if not request.user.is_authenticated:
        return {"unread_count": 0}
    return {
        "unread_count": request.user.notifications.filter(is_read=False).count()
    }
