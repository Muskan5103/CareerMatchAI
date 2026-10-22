
from django.urls import path
from . import views

urlpatterns = [
    path("", views.resume_list, name="resume_list"),
    path("upload/", views.resume_upload, name="resume_upload"),
    path("<int:pk>/primary/", views.set_primary_resume,
         name="set_primary_resume"),
    path("recommendations/", views.job_recommendations,
         name="job_recommendations"),
         path("<int:pk>/download/", views.download_resume, name="download_resume"),
]
