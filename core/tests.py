from django.contrib.auth import get_user_model
from django.test import TestCase


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='citizen',
            password='test-password-123',
        )

    def test_dashboard_redirects_to_login_when_signed_out(self):
        response = self.client.get('/')

        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_user_can_sign_in_and_open_dashboard(self):
        response = self.client.post(
            '/accounts/login/',
            {'username': 'citizen', 'password': 'test-password-123'},
        )

        self.assertRedirects(response, '/')
        dashboard_response = self.client.get('/')
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'Welcome, citizen')

    def test_invalid_credentials_do_not_sign_user_in(self):
        response = self.client.post(
            '/accounts/login/',
            {'username': 'citizen', 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incorrect')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_user_can_sign_out(self):
        self.client.force_login(self.user)
        response = self.client.post('/accounts/logout/')

        self.assertRedirects(response, '/accounts/login/')
        self.assertNotIn('_auth_user_id', self.client.session)

# Create your tests here.
