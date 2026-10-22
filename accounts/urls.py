
from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

urlpatterns = [
    path("register/candidate/", views.candidate_register,
         name="candidate_register"),

    path("register/recruiter/", views.recruiter_register,
         name="recruiter_register"),

    path("login/", views.user_login, name="login"),

    path("logout/", LogoutView.as_view(next_page="home"),
         name="logout"),

    path("candidate/dashboard/", views.candidate_dashboard,
         name="candidate_dashboard"),

    path("recruiter/dashboard/", views.recruiter_dashboard,
         name="recruiter_dashboard"),

path("candidate/profile/", views.candidate_profile, name="candidate_profile"),
path("recruiter/profile/", views.recruiter_profile, name="recruiter_profile"),
path(
    "admin/analytics/",
    views.admin_analytics,
    name="admin_analytics",
),

]
