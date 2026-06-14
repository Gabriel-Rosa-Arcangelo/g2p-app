from django.test import TestCase


class AccessControlTests(TestCase):
    def test_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get("/accounts/home/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
