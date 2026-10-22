from django.db import models
from django.conf import settings
from jobs.models import Job
from resumes.models import Resume


class JobApplication(models.Model):

    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        REVIEWING = "REVIEWING", "Under Review"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        INTERVIEW = "INTERVIEW", "Interview"
        REJECTED = "REJECTED", "Rejected"
        HIRED = "HIRED", "Hired"

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    cover_letter = models.TextField(blank=True)
    match_score = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPLIED,
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"],
                name="unique_candidate_job_application",
            )
        ]

    def __str__(self):
        return f"{self.candidate.username} - {self.job.title}"