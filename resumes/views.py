
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.models import User
from .forms import ResumeUploadForm
from .models import Resume
from .services import extract_resume_text, extract_skills


@login_required
@require_http_methods(["GET", "POST"])
def resume_list(request):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can manage resumes.")
        return redirect("home")

    resumes = Resume.objects.filter(
        candidate=request.user
    ).order_by("-is_primary", "-uploaded_at")

    return render(request, "resumes/resume_list.html", {
        "resumes": resumes,
    })


@login_required
@require_http_methods(["GET", "POST"])
def resume_upload(request):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can upload resumes.")
        return redirect("home")

    form = ResumeUploadForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        uploaded_file = form.cleaned_data["file"]

        try:
            extracted_text = extract_resume_text(
                uploaded_file,
                uploaded_file.name,
            )
            extracted_skills = extract_skills(extracted_text)
        except ValueError as exc:
            form.add_error("file", str(exc))
        else:
            with transaction.atomic():
                resume = form.save(commit=False)
                resume.candidate = request.user
                resume.extracted_text = extracted_text
                resume.extracted_skills = extracted_skills

                if resume.is_primary:
                    Resume.objects.filter(
                        candidate=request.user,
                        is_primary=True,
                    ).update(is_primary=False)
                elif not Resume.objects.filter(
                    candidate=request.user,
                    is_primary=True,
                ).exists():
                    resume.is_primary = True

                resume.save()

            messages.success(
                request,
                f"Resume uploaded. {len(extracted_skills)} skills detected.",
            )
            return redirect("resume_list")

    return render(request, "resumes/resume_upload.html", {
        "form": form,
    })


@login_required
@require_http_methods(["POST"])
def set_primary_resume(request, pk):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can manage resumes.")
        return redirect("home")

    resume = get_object_or_404(
        Resume,
        pk=pk,
        candidate=request.user,
    )

    with transaction.atomic():
        Resume.objects.filter(
            candidate=request.user,
            is_primary=True,
        ).update(is_primary=False)

        Resume.objects.filter(
            pk=resume.pk,
            candidate=request.user,
        ).update(is_primary=True)

    messages.success(request, "Primary resume updated.")
    return redirect("resume_list")



from jobs.models import Job
from .services import recommend_jobs


@login_required
def job_recommendations(request):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can view recommendations.")
        return redirect("home")

    resumes = Resume.objects.filter(
        candidate=request.user
    ).order_by("-is_primary", "-uploaded_at")

    resume_id = request.GET.get("resume")
    resume = resumes.filter(pk=resume_id).first() if resume_id else None

    if resume is None:
        resume = resumes.filter(is_primary=True).first() or resumes.first()

    if resume is None:
        messages.info(
            request,
            "Upload a resume before viewing job recommendations.",
        )
        return redirect("resume_upload")

    jobs = Job.objects.filter(is_active=True)
    recommendations = recommend_jobs(resume, jobs)

    return render(request, "resumes/job_recommendations.html", {
        "resume": resume,
        "resumes": resumes,
        "recommendations": recommendations,
    })



from django.http import FileResponse, Http404
from applications.models import JobApplication


@login_required
def download_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk)

    is_owner = (
        request.user.role == User.Role.CANDIDATE
        and resume.candidate_id == request.user.pk
    )

    is_authorized_recruiter = (
        request.user.role == User.Role.RECRUITER
        and JobApplication.objects.filter(
            resume=resume,
            job__recruiter=request.user,
        ).exists()
    )

    if not (is_owner or is_authorized_recruiter):
        raise Http404("Resume not found.")

    try:
        file_handle = resume.file.open("rb")
    except (OSError, ValueError):
        raise Http404("Resume file is unavailable.")

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=resume.file.name.split("/")[-1],
    )
