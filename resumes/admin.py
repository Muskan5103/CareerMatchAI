
from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "candidate",
        "is_primary",
        "uploaded_at",
    )
    list_filter = ("is_primary", "uploaded_at")
    search_fields = (
        "title",
        "candidate__username",
        "candidate__email",
    )
    readonly_fields = (
        "uploaded_at",
        "extracted_text",
        "extracted_skills",
    )
    list_per_page = 25
