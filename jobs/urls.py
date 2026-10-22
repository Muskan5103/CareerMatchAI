
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),

    path(
        "recruiter/jobs/",
        views.recruiter_job_list,
        name="recruiter_job_list",
    ),
    path(
        "recruiter/jobs/create/",
        views.job_create,
        name="job_create",
    ),
    path(
        "recruiter/jobs/<int:pk>/edit/",
        views.job_edit,
        name="job_edit",
    ),
    path(
        "recruiter/jobs/<int:pk>/toggle/",
        views.job_toggle_active,
        name="job_toggle_active",
    ),
    path(
        "recruiter/jobs/<int:pk>/applicants/",
        views.job_applicants,
        name="job_applicants",
    ),
    path(
        "my-applications/",
        views.my_applications,
        name="my_applications",
    ),
    path(
    "recruiter/jobs/<int:pk>/delete/",
    views.job_delete,
    name="job_delete",
),
]
