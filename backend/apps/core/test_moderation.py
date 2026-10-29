from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.accounts.test_career_api import candidate
from apps.companies.testing import recruiter
from apps.jobs.tests import create_job
from .models import ReviewDecision


class ModerationTests(APITestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(username="operator", is_staff=True)
        self.operator.user_permissions.add(Permission.objects.get(codename="moderate_marketplace"))
        self.recruiter = recruiter("pending@example.com", verified=False)
        self.company = self.recruiter.recruiter_profile.company
        self.recruiter.recruiter_profile.authority_declaration_at = timezone.now()
        self.recruiter.recruiter_profile.save()
        self.client.force_authenticate(self.operator)

    def decision(self, kind, item, **changes):
        values = {"decision": "approve", "reason": "Identity checked against submitted evidence", "method": "Operator document review", "expected_updated_at": item.updated_at.isoformat()}
        values.update(changes)
        return self.client.post(f"/api/operator/reviews/{kind}/{item.pk}/", values, format="json")

    def test_company_recruiter_and_publication_are_separate_audited_decisions(self):
        profile = self.recruiter.recruiter_profile
        self.assertEqual(self.decision("recruiter", profile).status_code, 400)
        self.assertEqual(self.decision("company", self.company).status_code, 201)
        self.assertEqual(self.decision("recruiter", profile).status_code, 201)
        job = create_job(self.company, posted_by=profile, status="draft", review_status="pending", review_requested_at=timezone.now())
        self.assertEqual(self.decision("job", job).status_code, 201)
        job.refresh_from_db()
        self.assertTrue(job.accepting_applications)
        record = ReviewDecision.objects.first()
        self.assertEqual(record.actor, self.operator)
        self.assertEqual(record.before["status"], "draft")
        self.assertEqual(record.after["status"], "published")
        self.assertEqual(ReviewDecision.objects.count(), 3)

    def test_stale_and_incomplete_decisions_do_not_mutate(self):
        self.company.description = "Changed after operator opened the queue"
        self.company.save()
        stale = self.company.updated_at
        self.company.save()
        self.assertEqual(self.decision("company", self.company, expected_updated_at=stale.isoformat()).status_code, 409)
        self.assertEqual(self.decision("company", self.company, reason="").status_code, 400)
        self.assertFalse(ReviewDecision.objects.exists())

    def test_rejection_keeps_job_private_and_returns_feedback(self):
        job = create_job(self.company, status="draft", review_status="pending", review_requested_at=timezone.now())
        self.assertEqual(self.decision("job", job, decision="reject", reason="Disclose salary period").status_code, 201)
        job.refresh_from_db()
        self.assertEqual(job.status, "draft")
        self.assertEqual(job.review_feedback, "Disclose salary period")
        self.assertEqual(self.client.get(f"/api/jobs/{job.slug}/").status_code, 404)

    def test_candidates_recruiters_and_unprivileged_staff_are_denied(self):
        for user in [candidate("unprivileged@example.com"), self.recruiter, get_user_model().objects.create_user(username="staff-only", is_staff=True)]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get("/api/operator/reviews/").status_code, 403)
            self.assertEqual(self.decision("company", self.company).status_code, 403)
        self.assertFalse(ReviewDecision.objects.exists())
