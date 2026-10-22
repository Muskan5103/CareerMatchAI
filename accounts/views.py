
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.db import transaction
from jobs.models import Job
from applications.models import JobApplication
from django.contrib.auth.decorators import user_passes_test

from resumes.models import Resume
from notifications.models import Notification

from .forms import CandidateProfileForm, RecruiterProfileForm
from .models import CandidateProfile, RecruiterProfile, User


from .forms import (
    CandidateRegistrationForm,
    RecruiterRegistrationForm,
)
from .models import CandidateProfile, RecruiterProfile, User


def role_home(user):
    if user.is_superuser:
        return redirect("admin_analytics")

    if user.role == User.Role.RECRUITER:
        return redirect("recruiter_dashboard")

    return redirect("candidate_dashboard")


@require_http_methods(["GET", "POST"])
def candidate_register(request):
    if request.user.is_authenticated:
        return role_home(request.user)

    form = CandidateRegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            CandidateProfile.objects.create(user=user)

        login(request, user)
        messages.success(request, "Your candidate account was created.")
        return role_home(user)

    return render(
        request,
        "accounts/register.html",
        {"form": form, "account_type": "Candidate"},
    )


@require_http_methods(["GET", "POST"])
def recruiter_register(request):
    if request.user.is_authenticated:
        return role_home(request.user)

    form = RecruiterRegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()

            RecruiterProfile.objects.create(
                user=user,
                company_name=form.cleaned_data["company_name"],
                designation=form.cleaned_data["designation"],
            )

        login(request, user)
        messages.success(request, "Your recruiter account was created.")
        return role_home(user)

    return render(
        request,
        "accounts/register.html",
        {"form": form, "account_type": "Recruiter"},
    )


@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.user.is_authenticated:
        return role_home(request.user)

    form = AuthenticationForm(
        request=request,
        data=request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)

        messages.success(request, "Welcome back!")
        return role_home(user)

    return render(
        request,
        "accounts/login.html",
        {"form": form},
    )


@login_required
def candidate_dashboard(request):
    if request.user.is_superuser:
        return redirect("admin_analytics")

    if request.user.role != User.Role.CANDIDATE:
        return role_home(request.user)

    return render(request, "accounts/dashboard.html", {
        "dashboard_title": "Candidate Dashboard",
        "dashboard_message": "Discover jobs that match your skills.",
    })



@login_required
def recruiter_dashboard(request):
    if request.user.is_superuser:
        return redirect("admin_analytics")

    if request.user.role != User.Role.RECRUITER:
        return role_home(request.user)

    recruiter_jobs = Job.objects.filter(recruiter=request.user)

    recruiter_applications = JobApplication.objects.filter(
        job__recruiter=request.user
    ).select_related("candidate", "job")

    status_counts = {
        "applied": recruiter_applications.filter(
            status=JobApplication.Status.APPLIED
        ).count(),
        "reviewing": recruiter_applications.filter(
            status=JobApplication.Status.REVIEWING
        ).count(),
        "shortlisted": recruiter_applications.filter(
            status=JobApplication.Status.SHORTLISTED
        ).count(),
        "interview": recruiter_applications.filter(
            status=JobApplication.Status.INTERVIEW
        ).count(),
        "rejected": recruiter_applications.filter(
            status=JobApplication.Status.REJECTED
        ).count(),
        "hired": recruiter_applications.filter(
            status=JobApplication.Status.HIRED
        ).count(),
    }

    context = {
        "dashboard_title": "Recruiter Dashboard",
        "dashboard_message": (
            "Monitor your vacancies and candidate applications."
        ),
        "total_jobs": recruiter_jobs.count(),
        "active_jobs": recruiter_jobs.filter(is_active=True).count(),
        "total_applications": recruiter_applications.count(),
        "status_counts": status_counts,
        "recent_applications": recruiter_applications.order_by(
            "-applied_at"
        )[:5],
    }

    return render(request, "accounts/dashboard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def candidate_profile(request):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "You cannot access that profile.")
        return role_home(request.user)

    profile, _ = CandidateProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = CandidateProfileForm(request.POST, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated.")
            return redirect("candidate_profile")
    else:
        form = CandidateProfileForm(
            instance=profile,
            initial={
                "skills": ", ".join(profile.skills or [])
            },
        )

    return render(request, "accounts/candidate_profile.html", {
        "form": form,
        "profile": profile,
    })


@login_required
@require_http_methods(["GET", "POST"])
def recruiter_profile(request):
    if request.user.role != User.Role.RECRUITER:
        messages.error(request, "You cannot access that profile.")
        return role_home(request.user)

    profile, _ = RecruiterProfile.objects.get_or_create(
        user=request.user,
        defaults={"company_name": ""},
    )

    if request.method == "POST":
        form = RecruiterProfileForm(request.POST, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Company profile updated.")
            return redirect("recruiter_profile")
    else:
        form = RecruiterProfileForm(instance=profile)

    return render(request, "accounts/recruiter_profile.html", {
        "form": form,
        "profile": profile,
    })

from django.contrib.auth.decorators import user_passes_test
@user_passes_test(
    lambda user: user.is_authenticated
    and user.is_active
    and user.is_superuser
)
@user_passes_test(
    lambda user: user.is_authenticated
    and user.is_active
    and user.is_superuser
)

def admin_analytics(request):
    total_candidates = User.objects.filter(
        role=User.Role.CANDIDATE
    ).count()

    total_recruiters = User.objects.filter(
        role=User.Role.RECRUITER
    ).count()

    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(is_active=True).count()

    total_applications = JobApplication.objects.count()

    status_counts = {
        status.value: JobApplication.objects.filter(
            status=status.value
        ).count()
        for status in JobApplication.Status
    }

    total_resumes = Resume.objects.count()
    total_notifications = Notification.objects.count()

    context = {
        "total_candidates": total_candidates,
        "total_recruiters": total_recruiters,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "total_resumes": total_resumes,
        "total_notifications": total_notifications,
        "status_counts": status_counts,
    }

    return render(
        request,
        "accounts/admin_analytics.html",
        context,
    )