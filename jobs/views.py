from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from applications.models import JobApplication
from .forms import JobForm
from .models import Job



# def home(request):
#     # Send superusers to platform analytics.
#     if request.user.is_authenticated and request.user.is_superuser:
#         return redirect("admin_analytics")

#     # Send recruiters to their own dashboard.
#     if (
#         request.user.is_authenticated
#         and request.user.role == User.Role.RECRUITER
#     ):
#         return redirect("recruiter_dashboard")

#     # Send candidates to their own dashboard.
#     if (
#         request.user.is_authenticated
#         and request.user.role == User.Role.CANDIDATE
#     ):
#         return redirect("candidate_dashboard")

#     # Public landing page for logged-out visitors.
#     jobs = Job.objects.filter(
#         is_active=True
#     ).select_related("recruiter")[:6]

#     return render(request, "jobs/home.html", {"jobs": jobs})
def home(request):
    jobs = Job.objects.filter(
        is_active=True
    ).select_related("recruiter")[:6]

    return render(request, "jobs/home.html", {"jobs": jobs})


def job_list(request):
    jobs = Job.objects.filter(is_active=True).select_related("recruiter")

    query = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    job_type = request.GET.get("job_type", "").strip()
    experience = request.GET.get("experience_level", "").strip()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company_name__icontains=query)
            | Q(description__icontains=query)
        )

    if location:
        jobs = jobs.filter(location__icontains=location)

    valid_job_types = {choice[0] for choice in Job.JobType.choices}
    if job_type in valid_job_types:
        jobs = jobs.filter(job_type=job_type)

    valid_experience = {
        choice[0] for choice in Job.ExperienceLevel.choices
    }
    if experience in valid_experience:
        jobs = jobs.filter(experience_level=experience)

    if request.user.is_authenticated and request.user.role == User.Role.CANDIDATE:
        applications = JobApplication.objects.filter(
            candidate=request.user,
            job=OuterRef("pk"),
        )
        jobs = jobs.annotate(has_applied=Exists(applications))
    else:
        jobs = jobs.annotate(has_applied=Exists(
            JobApplication.objects.none().filter(job=OuterRef("pk"))
        ))

    return render(request, "jobs/job_list.html", {
        "jobs": jobs,
        "query": query,
        "location": location,
        "selected_job_type": job_type,
        "selected_experience": experience,
        "job_types": Job.JobType.choices,
        "experience_levels": Job.ExperienceLevel.choices,
    })


from resumes.models import Resume
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    already_applied = False
    resumes = []

    if request.user.is_authenticated and request.user.role == User.Role.CANDIDATE:
        already_applied = JobApplication.objects.filter(
            candidate=request.user,
            job=job,
        ).exists()

        resumes = Resume.objects.filter(
            candidate=request.user
        ).order_by("-is_primary", "-uploaded_at")

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "already_applied": already_applied,
        "resumes": resumes,
    })



@login_required
def recruiter_job_list(request):
    if request.user.role != User.Role.RECRUITER:
        messages.error(request, "Only recruiters can manage job listings.")
        return redirect("candidate_dashboard")

    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by("-created_at")

    return render(request, "jobs/recruiter_job_list.html", {"jobs": jobs})


@login_required
def job_create(request):
    if request.user.role != User.Role.RECRUITER:
        messages.error(request, "Only recruiters can create jobs.")
        return redirect("candidate_dashboard")

    form = JobForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.recruiter = request.user
        job.save()

        messages.success(request, "Job listing created successfully.")
        return redirect("recruiter_job_list")

    return render(request, "jobs/job_form.html", {
        "form": form,
        "page_title": "Post a Job",
    })


@login_required
def job_edit(request, pk):
    if request.user.role != User.Role.RECRUITER:
        messages.error(request, "Only recruiters can edit jobs.")
        return redirect("candidate_dashboard")

    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    form = JobForm(request.POST or None, instance=job)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Job listing updated.")
        return redirect("recruiter_job_list")

    return render(request, "jobs/job_form.html", {
        "form": form,
        "page_title": "Edit Job",
        "job": job,
    })


@login_required
@require_POST
def job_toggle_active(request, pk):
    if request.user.role != User.Role.RECRUITER:
        messages.error(request, "Only recruiters can manage job listings.")
        return redirect("candidate_dashboard")

    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    job.is_active = not job.is_active
    job.save(update_fields=["is_active", "updated_at"])

    messages.success(
        request,
        "Job listing activated." if job.is_active else "Job listing deactivated.",
    )
    return redirect("recruiter_job_list")


# @login_required
# def job_applicants(request, pk):
#     if request.user.role != User.Role.RECRUITER:
#         messages.error(request, "Only recruiters can view applicants.")
#         return redirect("candidate_dashboard")

#     job = get_object_or_404(Job, pk=pk, recruiter=request.user)
#     applications = JobApplication.objects.filter(
#         job=job
#     ).select_related("candidate", "resume")

#     return render(request, "jobs/job_applicants.html", {
#         "job": job,
#         "applications": applications,
#     })


from django.shortcuts import render


@login_required
def my_applications(request):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can view their applications.")
        return redirect("home")

    applications = (
        JobApplication.objects
        .filter(candidate=request.user)
        .select_related("job", "resume")
        .order_by("-applied_at")
    )

    context = {
        "applications": applications,
    }

    return render(
        request,
        "jobs/my_applications.html",
        context,
    )


@login_required
def job_applicants(request, pk):
    # Allow recruiters only.
    if request.user.role != User.Role.RECRUITER:
        messages.error(
            request,
            "Only recruiters can view applicants."
        )
        return redirect("home")

    # A recruiter can access only their own job.
    job = get_object_or_404(
        Job,
        pk=pk,
        recruiter=request.user,
    )

    # Load applications belonging to this job.
    applications = (
        JobApplication.objects
        .filter(job=job)
        .select_related("candidate", "resume", "job")
        .order_by("-applied_at")
    )

    context = {
        "job": job,
        "applications": applications,
        "total_applicants": applications.count(),
        "status_choices": JobApplication.Status.choices,
    }

    return render(
        request,
        "jobs/job_applicants.html",
        context,
    )


@login_required
def job_delete(request, pk):
    if request.user.role != User.Role.RECRUITER:
        messages.error(request, "Only recruiters can delete jobs.")
        return redirect("candidate_dashboard")

    job = get_object_or_404(
        Job,
        pk=pk,
        recruiter=request.user,
    )

    if request.method == "POST":
        job.delete()
        messages.success(request, "Job listing deleted successfully.")
        return redirect("recruiter_job_list")

    return render(
        request,
        "jobs/job_confirm_delete.html",
        {"job": job},
    )