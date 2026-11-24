from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("universities/", include("universities.urls")),
    path("assessments/", include("assessments.urls")),
    path("analytics/", include("analytics.urls")),
    path("resources/", include("resources.urls")),
    path("dashboard/", include("dashboard.urls")),
]

handler404 = "core.views.error_404"
handler500 = "core.views.error_500"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
