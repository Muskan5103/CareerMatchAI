
from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company_name",
        "recruiter",
        "location",
        "job_type",
        "experience_level",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "job_type",
        "experience_level",
        "created_at",
    )
    search_fields = (
        "title",
        "company_name",
        "location",
        "recruiter__username",
    )
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25
