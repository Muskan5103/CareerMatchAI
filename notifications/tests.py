from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from applications.models import JobApplication
from jobs.models import Job
from .models import Notification




class NotificationAccessTests(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username="notification_candidate",
            email="candidate_notification@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.other_candidate = User.objects.create_user(
            username="other_notification_candidate",
            email="other_notification@example.com",
            password="TestPass123!",
            role=User.Role.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            username="notification_recruiter",
            email="recruiter_notification@example.com",
            password="TestPass123!",
            role=User.Role.RECRUITER,
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
        )

        self.notification = Notification.objects.create(
            recipient=self.candidate,
            application=self.application,
            message="Your application is under review.",
        )

    def test_candidate_can_view_own_notifications(self):
        self.client.force_login(self.candidate)

        response = self.client.get(reverse("notification_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "under review")
        self.assertEqual(response.context["unread_count"], 1)

    def test_candidate_cannot_view_another_candidates_notifications(self):
        self.client.force_login(self.other_candidate)

        response = self.client.get(reverse("notification_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "under review")
        self.assertEqual(response.context["unread_count"], 0)

    def test_candidate_can_mark_own_notification_as_read(self):
        self.client.force_login(self.candidate)

        response = self.client.post(
            reverse(
                "mark_notification_read",
                args=[self.notification.pk],
            )
        )

        self.assertRedirects(response, reverse("notification_list"))

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_candidate_cannot_mark_another_candidates_notification_as_read(self):
        self.client.force_login(self.other_candidate)

        response = self.client.post(
            reverse(
                "mark_notification_read",
                args=[self.notification.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

    def test_recruiter_cannot_view_candidate_notifications(self):
        self.client.force_login(self.recruiter)

        response = self.client.get(reverse("notification_list"))

        self.assertRedirects(response, reverse("home"))

    def test_get_request_cannot_mark_notification_as_read(self):
        self.client.force_login(self.candidate)

        response = self.client.get(
            reverse(
                "mark_notification_read",
                args=[self.notification.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)
