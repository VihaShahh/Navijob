from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.accounts.test_career_api import candidate
from apps.jobs.tests import create_company, create_job
from apps.jobs.testing import submitted_application
from .models import ListingReport, ReviewDecision


class ReportTests(APITestCase):
    def setUp(self):
        self.user = candidate("reporter@example.com")
        self.other = candidate("other-reporter@example.com")
        self.job = create_job(create_company(), application_mode="native", apply_url="")
        self.client.force_authenticate(self.user)

    def test_reports_are_private_and_duplicate_submission_is_idempotent(self):
        payload = {"job": self.job.pk, "category": "misleading", "details": "Salary seems incorrect", "reporter": self.other.pk, "status": "resolved"}
        self.assertEqual(self.client.post("/api/reports/", payload, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/reports/", payload, format="json").status_code, 200)
        self.assertEqual(ListingReport.objects.get().reporter, self.user)
        self.assertEqual(ListingReport.objects.get().status, "pending")
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/reports/").data, [])
        self.assertEqual(self.client.get("/api/operator/reports/").status_code, 403)

    def test_private_listing_and_blank_details_are_rejected(self):
        self.assertEqual(self.client.post("/api/reports/", {"job": self.job.pk, "category": "other", "details": " "}, format="json").status_code, 400)
        self.job.status = "draft"
        self.job.save()
        self.assertEqual(self.client.post("/api/reports/", {"job": self.job.pk, "category": "other", "details": "Test"}, format="json").status_code, 400)

    def test_operator_closure_preserves_applications_and_audits_resolution(self):
        application = submitted_application(self.user, self.job)
        report = ListingReport.objects.create(reporter=self.user, job=self.job, category="closed", details="No longer hiring")
        operator = get_user_model().objects.create_superuser(username="report-operator", password="local-test")
        self.client.force_authenticate(operator)
        response = self.client.post(f"/api/operator/reports/{report.pk}/", {"action": "close", "reason": "Confirmed closed with hiring team"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.job.refresh_from_db()
        self.assertFalse(self.job.accepting_applications)
        self.assertEqual(application.events.count(), 1)
        self.assertEqual(ReviewDecision.objects.get().after["job_status"], "closed")
        self.assertEqual(self.client.post(f"/api/operator/reports/{report.pk}/", {"action": "dismiss", "reason": "Late update"}, format="json").status_code, 409)
