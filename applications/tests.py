
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from jobs.models import Job
from .models import JobApplication
from notifications.models import Notification

class JobApplicationTests(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username="candidate_one",
            email="candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            username="recruiter_one",
            email="recruiter@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Python Developer",
            company_name="Example Tech",
            description="Django development.",
            required_skills=["Python"],
            location="Remote",
        )

    def test_candidate_can_apply(self):
        self.client.force_login(self.candidate)

        response = self.client.post(
            reverse("apply_for_job", args=[self.job.pk]),
            {"cover_letter": "I am interested in this role."},
        )

        self.assertRedirects(response, reverse("my_applications"))
        self.assertTrue(
            JobApplication.objects.filter(
                candidate=self.candidate, job=self.job
            ).exists()
        )

    def test_duplicate_application_is_prevented(self):
        JobApplication.objects.create(
            candidate=self.candidate, job=self.job
        )
        self.client.force_login(self.candidate)

        self.client.post(
            reverse("apply_for_job", args=[self.job.pk]),
            {"cover_letter": ""},
        )

        self.assertEqual(
            JobApplication.objects.filter(
                candidate=self.candidate, job=self.job
            ).count(),
            1,
        )

    def test_recruiter_cannot_apply(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            reverse("apply_for_job", args=[self.job.pk]),
            {"cover_letter": ""},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(
            JobApplication.objects.filter(job=self.job).exists()
        )

    def test_anonymous_user_cannot_apply(self):
        response = self.client.post(
            reverse("apply_for_job", args=[self.job.pk]),
            {"cover_letter": ""},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            JobApplication.objects.filter(job=self.job).exists()
        )





from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import User
from jobs.models import Job
from resumes.models import Resume
from .models import JobApplication


class ApplicationMatchingTests(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username="matching_candidate",
            email="matching@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            username="matching_recruiter",
            email="recruiter@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Python Developer",
            company_name="Example Tech",
            description="Develop Django web applications.",
            required_skills=["Python", "Django"],
            location="Remote",
        )

        self.resume = Resume.objects.create(
            candidate=self.candidate,
            title="Developer Resume",
            file=SimpleUploadedFile(
                "resume.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            extracted_text="Python Django web development",
            extracted_skills=["python", "django"],
            is_primary=True,
        )

    def test_application_saves_resume_and_match_score(self):
        self.client.force_login(self.candidate)

        response = self.client.post(
            reverse("apply_for_job", args=[self.job.pk]),
            {
                "resume_id": str(self.resume.pk),
                "cover_letter": "I am interested in this role.",
            },
        )

        self.assertRedirects(response, reverse("my_applications"))

        application = JobApplication.objects.get(
            candidate=self.candidate,
            job=self.job,
        )

        self.assertEqual(application.resume, self.resume)
        self.assertIsNotNone(application.match_score)
        self.assertGreaterEqual(application.match_score, 0)
        self.assertLessEqual(application.match_score, 100)

    def test_candidate_cannot_attach_another_users_resume(self):
        another_candidate = User.objects.create_user(
            username="other_candidate",
            email="other_candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.client.force_login(another_candidate)

        response = self.client.post(
            reverse("apply_for_job", args=[self.job.pk]),
            {"resume_id": str(self.resume.pk)},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            JobApplication.objects.filter(
                candidate=another_candidate,
                job=self.job,
            ).exists()
        )



class ApplicationStatusSecurityTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username="status_recruiter",
            email="recruiter@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.other_recruiter = User.objects.create_user(
            username="other_status_recruiter",
            email="other_recruiter@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.candidate = User.objects.create_user(
            username="status_candidate",
            email="candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Python Developer",
            company_name="Example Tech",
            description="Build Django applications.",
            required_skills=["Python", "Django"],
            location="Remote",
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            status=JobApplication.Status.APPLIED,
        )

        self.url = reverse(
            "update_application_status",
            args=[self.application.pk],
        )

    def test_owner_recruiter_can_update_status(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            self.url,
            {"status": JobApplication.Status.REVIEWING},
        )

        self.assertRedirects(
            response,
            reverse("job_applicants", args=[self.job.pk]),
        )

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.REVIEWING,
        )

    def test_other_recruiter_cannot_update_status(self):
        self.client.force_login(self.other_recruiter)

        response = self.client.post(
            self.url,
            {"status": JobApplication.Status.SHORTLISTED},
        )

        self.assertEqual(response.status_code, 404)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.APPLIED,
        )

    def test_candidate_cannot_update_status(self):
        self.client.force_login(self.candidate)

        response = self.client.post(
            self.url,
            {"status": JobApplication.Status.HIRED},
        )

        self.assertRedirects(response, reverse("home"))

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.APPLIED,
        )

    def test_invalid_status_is_rejected(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            self.url,
            {"status": "INVALID_STATUS"},
        )

        self.assertRedirects(
            response,
            reverse("job_applicants", args=[self.job.pk]),
        )

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.APPLIED,
        )

    def test_get_request_cannot_update_status(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(
            self.url,
            {"status": JobApplication.Status.REJECTED},
        )

        self.assertEqual(response.status_code, 405)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            JobApplication.Status.APPLIED,
        )

    def test_status_change_creates_candidate_notification(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            self.url,
            {"status": JobApplication.Status.SHORTLISTED},
        )

        self.assertEqual(response.status_code, 302)

        notification = Notification.objects.get(
            recipient=self.candidate,
            application=self.application,
        )

        self.assertIn("Shortlisted", notification.message)
        self.assertFalse(notification.is_read)


    def test_unchanged_status_does_not_create_notification(self):
        self.client.force_login(self.recruiter)

        self.client.post(
            self.url,
            {"status": JobApplication.Status.APPLIED},
        )

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.candidate,
                application=self.application,
            ).exists()
        )


    def test_candidate_does_not_receive_notification_for_another_application(self):
        self.client.force_login(self.recruiter)

        self.client.post(
            self.url,
            {"status": JobApplication.Status.REVIEWING},
        )

        self.assertEqual(
            Notification.objects.filter(
                recipient=self.candidate,
                application=self.application,
            ).count(),
            1,
        )

class MyApplicationsAccessTests(TestCase):
    def setUp(self):
        self.candidate_one = User.objects.create_user(
            username="tracking_candidate_one",
            email="tracking1@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.candidate_two = User.objects.create_user(
            username="tracking_candidate_two",
            email="tracking2@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.recruiter = User.objects.create_user(
            username="tracking_recruiter",
            email="tracking_recruiter@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Tracking Test Developer",
            company_name="Tracking Test Company",
            description="A test job for application tracking.",
            required_skills=["Python"],
            location="Remote",
        )

        self.application_one = JobApplication.objects.create(
            candidate=self.candidate_one,
            job=self.job,
            status=JobApplication.Status.SHORTLISTED,
            match_score=85.0,
        )

        self.url = reverse("my_applications")

    def test_candidate_sees_own_applications(self):
        self.client.force_login(self.candidate_one)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tracking Test Developer")
        self.assertContains(response, "Shortlisted")
        self.assertContains(response, "85.0%")

        self.assertEqual(
            list(response.context["applications"]),
            [self.application_one],
        )

    def test_candidate_cannot_see_another_candidates_applications(self):
        self.client.force_login(self.candidate_two)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tracking Test Developer")
        self.assertEqual(
            response.context["applications"].count(),
            0,
        )

    def test_recruiter_cannot_access_candidate_tracking_page(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("home"))

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
