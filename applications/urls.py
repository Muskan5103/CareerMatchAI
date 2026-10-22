
from django.urls import path
from . import views

urlpatterns = [
    path("apply/<int:pk>/", views.apply_for_job, name="apply_for_job"),
    path(
        "<int:application_id>/status/",
        views.update_application_status,
        name="update_application_status",
    ),
]
