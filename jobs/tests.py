
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Job
from applications.models import JobApplication


class JobPortalTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username="recruiter_one",
            email="recruiter@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.other_recruiter = User.objects.create_user(
            username="recruiter_two",
            email="recruiter2@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.candidate = User.objects.create_user(
            username="candidate_one",
            email="candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Junior Python Developer",
            company_name="Example Tech",
            description="Develop Django applications.",
            required_skills=["Python", "Django"],
            location="Amritsar",
        )

    def test_active_job_appears_in_job_list(self):
        response = self.client.get(reverse("job_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Junior Python Developer")

    def test_job_search_filters_by_location(self):
        response = self.client.get(
            reverse("job_list"), {"location": "Amritsar"}
        )
        self.assertContains(response, "Junior Python Developer")

        response = self.client.get(
            reverse("job_list"), {"location": "Delhi"}
        )
        self.assertNotContains(response, "Junior Python Developer")

    def test_candidate_cannot_create_job(self):
        self.client.force_login(self.candidate)
        response = self.client.get(reverse("job_create"))

        self.assertRedirects(
            response, reverse("candidate_dashboard")
        )

    def test_recruiter_cannot_edit_another_recruiters_job(self):
        self.client.force_login(self.other_recruiter)

        response = self.client.get(
            reverse("job_edit", args=[self.job.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_inactive_job_is_not_public(self):
        self.job.is_active = False
        self.job.save()

        response = self.client.get(
            reverse("job_detail", args=[self.job.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_recruiter_can_create_job(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            reverse("job_create"),
            {
                "title": "Django Developer",
                "company_name": "Example Tech",
                "description": "Build web applications.",
                "required_skills": "Python, Django, SQL",
                "location": "Remote",
                "job_type": "FULL_TIME",
                "experience_level": "FRESHER",
                "min_salary": "20000",
                "max_salary": "40000",
            },
        )

        self.assertRedirects(
            response, reverse("recruiter_job_list")
        )

        job = Job.objects.get(title="Django Developer")
        self.assertEqual(job.recruiter, self.recruiter)
        self.assertEqual(
            job.required_skills, ["Python", "Django", "SQL"]
        )


class RecruiterApplicantAccessTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username="recruiter_stage6",
            email="recruiter6@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.other_recruiter = User.objects.create_user(
            username="other_recruiter_stage6",
            email="other6@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.candidate = User.objects.create_user(
            username="candidate_stage6",
            email="candidate6@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Python Developer",
            company_name="Example Tech",
            description="Develop Django applications.",
            required_skills=["Python", "Django"],
            location="Remote",
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            cover_letter="I have experience with Python and Django.",
            match_score=85.0,
        )

    def test_owner_recruiter_can_view_applicants(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(
            reverse("job_applicants", args=[self.job.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "jobs/job_applicants.html"
        )
        self.assertContains(response, "candidate_stage6")
        self.assertContains(response, "85.0%")

    def test_other_recruiter_gets_404(self):
        self.client.force_login(self.other_recruiter)

        response = self.client.get(
            reverse("job_applicants", args=[self.job.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_candidate_is_redirected(self):
        self.client.force_login(self.candidate)

        response = self.client.get(
            reverse("job_applicants", args=[self.job.pk])
        )

        self.assertRedirects(response, reverse("home"))

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("job_applicants", args=[self.job.pk])
        )

        self.assertEqual(response.status_code, 302)

    def test_applicant_list_does_not_show_other_jobs(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(
            reverse("job_applicants", args=[self.job.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["applications"]),
            [self.application],
        )



class RecruiterJobManagementSecurityTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username="manage_owner",
            email="manage_owner@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.other_recruiter = User.objects.create_user(
            username="manage_other",
            email="manage_other@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.candidate = User.objects.create_user(
            username="manage_candidate",
            email="manage_candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Original Python Job",
            company_name="Example Company",
            description="Original description.",
            required_skills=["Python"],
            location="Remote",
        )

    def test_owner_can_edit_job(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            reverse("job_edit", args=[self.job.pk]),
            {
                "title": "Updated Python Job",
                "company_name": "Example Company",
                "description": "Updated description.",
                "required_skills": "Python, Django",
                "location": "Remote",
                "job_type": Job.JobType.FULL_TIME,
                "experience_level": Job.ExperienceLevel.FRESHER,
                "min_salary": "30000",
                "max_salary": "60000",
            },
        )

        self.assertRedirects(response, reverse("recruiter_job_list"))
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Updated Python Job")
        self.assertEqual(self.job.required_skills, ["Python", "Django"])

    def test_other_recruiter_cannot_edit_job(self):
        self.client.force_login(self.other_recruiter)

        response = self.client.get(reverse("job_edit", args=[self.job.pk]))

        self.assertEqual(response.status_code, 404)

    def test_candidate_cannot_edit_job(self):
        self.client.force_login(self.candidate)

        response = self.client.get(reverse("job_edit", args=[self.job.pk]))

        self.assertRedirects(response, reverse("candidate_dashboard"))

    def test_owner_can_deactivate_job(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            reverse("job_toggle_active", args=[self.job.pk])
        )

        self.assertRedirects(response, reverse("recruiter_job_list"))
        self.job.refresh_from_db()
        self.assertFalse(self.job.is_active)

    def test_other_recruiter_cannot_toggle_job(self):
        self.client.force_login(self.other_recruiter)

        response = self.client.post(
            reverse("job_toggle_active", args=[self.job.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.job.refresh_from_db()
        self.assertTrue(self.job.is_active)

    def test_get_request_cannot_toggle_job(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(
            reverse("job_toggle_active", args=[self.job.pk])
        )

        self.assertEqual(response.status_code, 405)
        self.job.refresh_from_db()
        self.assertTrue(self.job.is_active)


class RecruiterJobDeletionSecurityTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user(
            username="delete_owner",
            email="delete_owner@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.other_recruiter = User.objects.create_user(
            username="delete_other",
            email="delete_other@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.candidate = User.objects.create_user(
            username="delete_candidate",
            email="delete_candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Job To Delete",
            company_name="Example Company",
            description="A test job listing.",
            required_skills=["Python"],
            location="Remote",
        )

        self.url = reverse("job_delete", args=[self.job.pk])

    def test_owner_can_view_delete_confirmation(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/job_confirm_delete.html")
        self.assertContains(response, "Job To Delete")

        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())

    def test_owner_can_delete_job_using_post(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(self.url)

        self.assertRedirects(
            response,
            reverse("recruiter_job_list"),
        )
        self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())

    def test_other_recruiter_cannot_delete_job(self):
        self.client.force_login(self.other_recruiter)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())

    def test_candidate_cannot_delete_job(self):
        self.client.force_login(self.candidate)

        response = self.client.post(self.url)

        self.assertRedirects(
            response,
            reverse("candidate_dashboard"),
        )
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())

    def test_get_request_does_not_delete_job(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())
