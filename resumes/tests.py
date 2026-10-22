
from io import BytesIO
from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, SimpleTestCase
from django.urls import reverse

from docx import Document

from accounts.models import User
from .forms import ResumeUploadForm
from . import services
from .services import extract_resume_text, calculate_job_match
from .models import Resume
from jobs.models import Job


class ResumeServiceTests(SimpleTestCase):


    def test_extract_skills(self):
        text = "Built web apps using Python, Django and PostgreSQL."

        skills = services.extract_skills(text)

        print("Skills detected by test:", skills)
        print("Skill list:", services.SKILL_TERMS)

        self.assertIn("python", skills)
        self.assertIn("django", skills)
        self.assertIn("postgresql", skills)



    def test_extract_docx_text(self):
        buffer = BytesIO()
        document = Document()
        document.add_paragraph("Python Django PostgreSQL")
        document.save(buffer)
        buffer.seek(0)

        text = extract_resume_text(buffer, "resume.docx")

        self.assertIn("Python", text)
        self.assertIn("Django", text)

    def test_reject_unsupported_extension(self):
        with self.assertRaises(ValueError):
            extract_resume_text(
                BytesIO(b"not a document"),
                "resume.txt",
            )

    def test_reject_non_pdf_content(self):
        upload = SimpleUploadedFile(
            "resume.pdf",
            b"this is not a PDF",
        )
        form = ResumeUploadForm(data={"title": "Test"}, files={
            "file": upload,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)


class ResumeAccessTests(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username="resume_owner",
            email="owner@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.other_candidate = User.objects.create_user(
            username="another_candidate",
            email="other@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.resume = Resume.objects.create(
            candidate=self.candidate,
            title="Python Resume",
            file=SimpleUploadedFile(
                "resume.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            extracted_text="Python Django PostgreSQL",
            extracted_skills=["python", "django", "postgresql"],
            is_primary=True,
        )

    def test_candidate_can_view_own_resume_list(self):
        self.client.force_login(self.candidate)
        response = self.client.get(reverse("resume_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Resume")

    def test_candidate_cannot_download_another_candidates_resume(self):
        self.client.force_login(self.other_candidate)

        response = self.client.get(
            reverse("download_resume", args=[self.resume.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_download_resume(self):
        self.client.force_login(self.candidate)

        response = self.client.get(
            reverse("download_resume", args=[self.resume.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"].split(";")[0],
                         "attachment")


class JobMatchingTests(TestCase):
    def test_matching_returns_score_and_skill_gap(self):
        resume = SimpleNamespace(
            extracted_text="Python Django PostgreSQL web development",
            extracted_skills=["python", "django", "postgresql"],
        )
        job = SimpleNamespace(
            title="Python Developer",
            company_name="Example Tech",
            description="Build Django web APIs",
            required_skills=["Python", "Django", "REST API"],
        )

        result = calculate_job_match(resume, job)

        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertIn("python", result["matched_skills"])
        self.assertIn("rest api", result["missing_skills"])
