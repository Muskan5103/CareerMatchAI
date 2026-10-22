from django.db import models
from django.conf import settings


class Resume(models.Model):
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    title = models.CharField(max_length=150, default="My Resume")
    file = models.FileField(upload_to="resumes/%Y/%m/")
    extracted_text = models.TextField(blank=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.candidate.username}"