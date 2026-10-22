
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.models import User
from jobs.models import Job
from .models import JobApplication



from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.models import User
from jobs.models import Job
from resumes.models import Resume
from resumes.services import calculate_job_match
from .models import JobApplication


@login_required
@require_POST
def apply_for_job(request, pk):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can apply for jobs.")
        return redirect("home")

    job = get_object_or_404(Job, pk=pk, is_active=True)

    cover_letter = request.POST.get("cover_letter", "").strip()

    if len(cover_letter) > 5000:
        messages.error(request, "Cover letter must be 5,000 characters or fewer.")
        return redirect("job_detail", pk=job.pk)

    if JobApplication.objects.filter(
        candidate=request.user,
        job=job,
    ).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect("job_detail", pk=job.pk)

    resume = None
    resume_id = request.POST.get("resume_id", "").strip()

    if resume_id:
        resume = get_object_or_404(
            Resume,
            pk=resume_id,
            candidate=request.user,
        )
    else:
        resume = Resume.objects.filter(
            candidate=request.user,
            is_primary=True,
        ).first()

    match_score = None

    if resume:
        match_score = calculate_job_match(resume, job)["score"]

    try:
        with transaction.atomic():
            JobApplication.objects.create(
                candidate=request.user,
                job=job,
                resume=resume,
                cover_letter=cover_letter,
                match_score=match_score,
            )
    except IntegrityError:
        messages.info(request, "You have already applied for this job.")
        return redirect("job_detail", pk=job.pk)

    messages.success(request, "Your application was submitted.")
    return redirect("my_applications")



from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from accounts.models import User
from applications.models import JobApplication
from notifications.models import Notification

@login_required
@require_POST
def update_application_status(request, application_id):
    # Only recruiters can update application statuses.
    if request.user.role != User.Role.RECRUITER:
        messages.error(request, "Only recruiters can update application status.")
        return redirect("home")

    # A recruiter can update applications only for their own jobs.
    application = get_object_or_404(
        JobApplication,
        pk=application_id,
        job__recruiter=request.user,
    )

    new_status = request.POST.get("status", "").strip()

    # Reject invalid or tampered status values.
    if new_status not in JobApplication.Status.values:
        messages.error(request, "Invalid application status.")
        return redirect("job_applicants", pk=application.job_id)

    old_status = application.status

    if old_status != new_status:
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])

        Notification.objects.create(
            recipient=application.candidate,
            application=application,
            message=(
                f'Your application for "{application.job.title}" '
                f'has been updated to '
                f'{application.get_status_display()}.'
            ),
        )

    messages.success(request, "Application status updated successfully.")
    return redirect("job_applicants", pk=application.job_id)
