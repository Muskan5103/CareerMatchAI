
from django.test import TestCase
from django.urls import reverse

from .models import User, CandidateProfile, RecruiterProfile
from django.test import TestCase
from django.urls import reverse
from resumes.models import Resume
from notifications.models import Notification
from accounts.models import User
from jobs.models import Job
from applications.models import JobApplication

class ProfileManagementTests(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username="candidate1",
            email="candidate1@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate,
            full_name="Candidate One",
            skills=["Python"],
        )

        self.recruiter = User.objects.create_user(
            username="recruiter1",
            email="recruiter1@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter,
            company_name="Example Company",
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("candidate_profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_candidate_can_view_own_profile(self):
        self.client.force_login(self.candidate)
        response = self.client.get(reverse("candidate_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Candidate One")

    def test_candidate_can_update_own_profile(self):
        self.client.force_login(self.candidate)

        response = self.client.post(
            reverse("candidate_profile"),
            {
                "full_name": "Updated Candidate",
                "phone": "9876543210",
                "location": "Amritsar",
                "education": "BCA",
                "skills": "Python, Django, PostgreSQL",
                "experience_years": 1,
                "linkedin_url": "",
                "github_url": "",
            },
        )

        self.assertRedirects(response, reverse("candidate_profile"))

        self.candidate_profile.refresh_from_db()
        self.assertEqual(
            self.candidate_profile.full_name, "Updated Candidate"
        )
        self.assertEqual(
            self.candidate_profile.skills,
            ["Python", "Django", "PostgreSQL"],
        )

    def test_recruiter_cannot_access_candidate_profile(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(reverse("candidate_profile"))

        self.assertRedirects(
            response, reverse("recruiter_dashboard")
        )

    def test_candidate_cannot_access_recruiter_profile(self):
        self.client.force_login(self.candidate)

        response = self.client.get(reverse("recruiter_profile"))

        self.assertRedirects(
            response, reverse("candidate_dashboard")
        )

    def test_recruiter_can_update_company_profile(self):
        self.client.force_login(self.recruiter)

        response = self.client.post(
            reverse("recruiter_profile"),
            {
                "company_name": "Updated Company",
                "designation": "HR Manager",
                "company_website": "https://example.com",
                "company_description": "Technology company",
            },
        )

        self.assertRedirects(response, reverse("recruiter_profile"))

        self.recruiter_profile.refresh_from_db()
        self.assertEqual(
            self.recruiter_profile.company_name, "Updated Company"
        )




class RecruiterDashboardAnalyticsTests(TestCase):
    def setUp(self):
        self.recruiter_one = User.objects.create_user(
            username="analytics_recruiter_one",
            email="analytics1@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.recruiter_two = User.objects.create_user(
            username="analytics_recruiter_two",
            email="analytics2@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.candidate_one = User.objects.create_user(
            username="analytics_candidate_one",
            email="candidate1@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.candidate_two = User.objects.create_user(
            username="analytics_candidate_two",
            email="candidate2@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.job_one = Job.objects.create(
            recruiter=self.recruiter_one,
            title="Recruiter One Python Job",
            company_name="Company One",
            description="Python development.",
            required_skills=["Python"],
            location="Remote",
        )

        self.job_two = Job.objects.create(
            recruiter=self.recruiter_two,
            title="Recruiter Two Django Job",
            company_name="Company Two",
            description="Django development.",
            required_skills=["Django"],
            location="Remote",
        )

        self.application_one = JobApplication.objects.create(
            candidate=self.candidate_one,
            job=self.job_one,
            status=JobApplication.Status.SHORTLISTED,
            match_score=85.0,
        )

        JobApplication.objects.create(
            candidate=self.candidate_two,
            job=self.job_two,
            status=JobApplication.Status.HIRED,
            match_score=90.0,
        )

        self.url = reverse("recruiter_dashboard")

    def test_dashboard_shows_only_logged_in_recruiters_data(self):
        self.client.force_login(self.recruiter_one)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_jobs"], 1)
        self.assertEqual(response.context["active_jobs"], 1)
        self.assertEqual(response.context["total_applications"], 1)

        self.assertEqual(response.context["status_counts"]["shortlisted"], 1)
        self.assertEqual(response.context["status_counts"]["hired"], 0)

        recent = list(response.context["recent_applications"])
        self.assertEqual(recent, [self.application_one])

        self.assertContains(response, "Recruiter One Python Job")
        self.assertNotContains(response, "Recruiter Two Django Job")
        self.assertNotContains(response, "analytics_candidate_two")

    def test_candidate_cannot_access_recruiter_dashboard(self):
        self.client.force_login(self.candidate_one)

        response = self.client.get(self.url)

        self.assertRedirects(
            response,
            reverse("candidate_dashboard"),
        )




class AdminAnalyticsAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="analytics_admin",
            email="analytics_admin@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.candidate = User.objects.create_user(
            username="regular_candidate",
            email="regular_candidate@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )

        self.recruiter = User.objects.create_user(
            username="regular_recruiter",
            email="regular_recruiter@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
        )

        self.job = Job.objects.create(
            recruiter=self.recruiter,
            title="Analytics Test Developer",
            company_name="Example Company",
            description="Python development.",
            required_skills=["Python"],
            location="Remote",
        )

        self.application = JobApplication.objects.create(
            candidate=self.candidate,
            job=self.job,
            status=JobApplication.Status.APPLIED,
        )

        self.url = reverse("admin_analytics")

    def test_superuser_can_view_platform_analytics(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/admin_analytics.html",
        )
        self.assertEqual(response.context["total_candidates"], 2)
        self.assertEqual(response.context["total_recruiters"], 1)
        self.assertEqual(response.context["total_jobs"], 1)
        self.assertEqual(response.context["active_jobs"], 1)
        self.assertEqual(response.context["total_applications"], 1)
        self.assertEqual(response.context["status_counts"]["APPLIED"], 1)

    def test_candidate_cannot_view_platform_analytics(self):
        self.client.force_login(self.candidate)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_recruiter_cannot_view_platform_analytics(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_cannot_view_platform_analytics(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
