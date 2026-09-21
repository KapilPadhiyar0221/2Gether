"""Friendly error pages. Users never see a Django traceback."""
from django.shortcuts import render


def not_found(request, exception=None):
    return render(request, "errors/error.html", {
        "code": "404",
        "title": "That page isn't here",
        "detail": "The link may be old, or the post may have been deleted.",
    }, status=404)


def forbidden(request, exception=None):
    return render(request, "errors/error.html", {
        "code": "403",
        "title": "You don't have access to this",
        "detail": "Sign in with the right account, or head back to your feed.",
    }, status=403)


def server_error(request):
    return render(request, "errors/error.html", {
        "code": "500",
        "title": "Something broke on our side",
        "detail": "Nothing you did. Try again in a moment.",
    }, status=500)
