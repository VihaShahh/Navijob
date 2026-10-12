from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.accounts.test_career_api import candidate
from apps.jobs.testing import submitted_application
from apps.jobs.tests import create_company, create_job
from .models import DeletionRequest


class DeletionTests(APITestCase):
    def setUp(self):
        self.user = candidate("delete@example.com")
        self.other = candidate("other-delete@example.com")
        self.client.force_authenticate(self.user)

    def test_request_is_explicit_owner_scoped_and_cancellable(self):
        self.assertEqual(self.client.post("/api/me/deletion/", {}, format="json").status_code, 400)
        payload = {"confirmation": "REQUEST DELETION", "user": self.other.pk, "status": "access_disabled"}
        response = self.client.post("/api/me/deletion/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        item = DeletionRequest.objects.get()
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.status, "pending")
        self.assertEqual(self.client.post("/api/me/deletion/", payload, format="json").status_code, 200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/me/deletion/").data, [])
        self.assertEqual(self.client.post(f"/api/me/deletion/{item.pk}/cancel/").status_code, 404)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(f"/api/me/deletion/{item.pk}/cancel/").status_code, 200)

    def test_operator_review_disables_access_without_claiming_erasure(self):
        application = submitted_application(self.user, create_job(create_company(), application_mode="native", apply_url=""))
        item = DeletionRequest.objects.create(user=self.user)
        self.assertEqual(self.client.post(f"/api/operator/deletion/{item.pk}/", {"action": "disable_access", "reason": "Review required"}, format="json").status_code, 403)
        operator = get_user_model().objects.create_superuser(username="deletion-operator", password="local-test")
        self.client.force_authenticate(operator)
        response = self.client.post(f"/api/operator/deletion/{item.pk}/", {"action": "disable_access", "reason": "Access removed; retention and file erasure pending"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "access_disabled")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        application.refresh_from_db()
        self.assertTrue(application.resume_snapshot_file.storage.exists(application.resume_snapshot_file.name))
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/me/export/").status_code, 403)
