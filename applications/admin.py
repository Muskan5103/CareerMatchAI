
from django.contrib import admin
from .models import JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "candidate",
        "job",
        "status",
        "match_score",
        "applied_at",
        "updated_at",
    )
    list_filter = ("status", "applied_at", "updated_at")
    search_fields = (
        "candidate__username",
        "candidate__email",
        "job__title",
        "job__company_name",
    )
    readonly_fields = ("applied_at", "updated_at")
    date_hierarchy = "applied_at"
    list_per_page = 25
