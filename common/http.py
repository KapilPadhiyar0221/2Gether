"""Request helpers shared by every app."""


def wants_json(request):
    """True when our own fetch() made the call, rather than a browser navigation."""
    return request.headers.get("X-Requested-With") == "fetch"
