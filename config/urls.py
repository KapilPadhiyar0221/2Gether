from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config import errors

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("posts.urls")),
    path("", include("accounts.urls")),
    path("notifications/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = errors.not_found
handler403 = errors.forbidden
handler500 = errors.server_error
