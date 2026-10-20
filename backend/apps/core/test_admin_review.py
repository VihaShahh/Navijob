from types import SimpleNamespace
from django.contrib.admin import AdminSite
from django.test import TestCase
from apps.companies.admin import CompanyAdmin
from apps.companies.models import Company
from apps.jobs.admin import JobAdmin
from apps.jobs.models import Job
from apps.jobs.tests import create_company, create_job


class AdminReviewTests(TestCase):
    def test_admin_job_edits_cannot_keep_unreviewed_content_published(self):
        job = create_job(create_company())
        job.description = "New content written through admin"
        JobAdmin(Job, AdminSite()).save_model(None, job, SimpleNamespace(changed_data=["description"]), True)
        job.refresh_from_db()
        self.assertEqual(job.status, "draft")
        self.assertEqual(job.review_status, "pending")
        self.assertIsNone(job.review_requested_at)
        self.assertEqual(Job.objects.available().count(), 0)

    def test_admin_identity_edit_invalidates_old_company_review(self):
        company = create_company()
        create_job(company)
        company.website = "https://changed.example.com"
        CompanyAdmin(Company, AdminSite()).save_model(None, company, SimpleNamespace(changed_data=["website"]), True)
        company.refresh_from_db()
        self.assertFalse(company.is_verified)
        self.assertEqual(company.review_status, "pending")
        self.assertEqual(Job.objects.available().count(), 0)
