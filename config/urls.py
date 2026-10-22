from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("jobs.urls")),
    path("accounts/", include("accounts.urls")),
    path("applications/", include("applications.urls")),
    path("resumes/", include("resumes.urls")),
    path(
    "notifications/",
    include("notifications.urls"),
),
]

FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024