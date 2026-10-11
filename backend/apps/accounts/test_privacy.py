import json
from rest_framework.test import APITestCase
from apps.accounts.test_career_api import candidate
from apps.jobs.models import ApplicationNote
from apps.jobs.tests import create_company, create_job
from apps.jobs.testing import submitted_application


class PrivacyTests(APITestCase):
    def setUp(self):
        self.user = candidate("export@example.com")
        self.other = candidate("other-export@example.com")
        self.client.force_authenticate(self.user)

    def test_preferences_are_owner_scoped_and_cannot_publish_profiles(self):
        response = self.client.patch("/api/me/privacy/", {"is_open_to_work": False, "public_visibility": True, "user": self.other.pk}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["public_visibility"])
        self.user.applicant_profile.refresh_from_db()
        self.other.applicant_profile.refresh_from_db()
        self.assertFalse(self.user.applicant_profile.is_open_to_work)
        self.assertTrue(self.other.applicant_profile.is_open_to_work)

    def test_export_excludes_other_accounts_private_notes_and_credentials(self):
        job = create_job(create_company(), application_mode="native", apply_url="")
        application = submitted_application(self.user, job)
        ApplicationNote.objects.create(application=application, author=self.other, body="Employer confidential note")
        submitted_application(self.other, job)
        response = self.client.get("/api/me/export/", {"user": self.other.pk})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["applications"]), 1)
        self.assertEqual(data["account"]["email"], self.user.email)
        self.assertNotIn(self.other.email, response.content.decode())
        self.assertNotIn("Employer confidential note", response.content.decode())
        self.assertNotIn(self.user.password, response.content.decode())
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_anonymous_export_and_preferences_are_denied(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/me/export/").status_code, 403)
        self.assertEqual(self.client.get("/api/me/privacy/").status_code, 403)
