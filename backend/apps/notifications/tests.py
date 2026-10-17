from rest_framework.test import APITestCase
from apps.accounts.test_career_api import candidate
from apps.companies.testing import recruiter
from apps.jobs.models import ApplicationNote
from apps.jobs.testing import submitted_application
from apps.jobs.tests import create_job
from apps.jobs.transitions import move_application
from .models import ApplicationUpdate


class UpdateTests(APITestCase):
    def setUp(self):
        self.user = candidate("updates@example.com")
        self.other = candidate("other-updates@example.com")
        self.recruiter = recruiter("update-recruiter@example.com")
        self.application = submitted_application(self.user, create_job(self.recruiter.recruiter_profile.company, application_mode="native", apply_url=""))

    def test_application_events_create_scoped_updates_and_private_notes_do_not(self):
        self.assertEqual(ApplicationUpdate.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ApplicationUpdate.objects.filter(user=self.recruiter).count(), 1)
        ApplicationNote.objects.create(application=self.application, author=self.recruiter, body="Confidential hiring discussion")
        self.assertEqual(ApplicationUpdate.objects.count(), 2)
        move_application(self.application, self.recruiter, "reviewing", "submitted")
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/updates/")
        self.assertEqual(response.data["unread_count"], 2)
        self.assertNotIn("Confidential hiring discussion", str(response.data))

    def test_read_status_is_idempotent_and_other_accounts_cannot_change_it(self):
        item = ApplicationUpdate.objects.get(user=self.user)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/updates/").data["results"], [])
        self.assertEqual(self.client.post(f"/api/updates/{item.pk}/read/").status_code, 404)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(f"/api/updates/{item.pk}/read/").status_code, 200)
        item.refresh_from_db()
        read_at = item.read_at
        self.client.post(f"/api/updates/{item.pk}/read/")
        item.refresh_from_db()
        self.assertEqual(item.read_at, read_at)
        self.assertEqual(self.client.get("/api/updates/").data["unread_count"], 0)
