from rest_framework.test import APITestCase


class ApiCacheTests(APITestCase):
    def test_session_csrf_and_permission_failures_are_not_cacheable(self):
        for path in ["/api/auth/session/", "/api/auth/csrf/", "/api/operator/reviews/", "/api/me/export/", "/api/resumes/"]:
            response = self.client.get(path)
            self.assertIn(response.status_code, [200, 403])
            self.assertEqual(response["Cache-Control"], "private, no-store")
