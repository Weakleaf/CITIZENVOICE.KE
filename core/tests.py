from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import UserProfile


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
        self.assertContains(dashboard_response, 'Citizen')
        self.assertContains(dashboard_response, 'Account status')

    def test_citizen_can_register(self):
        response = self.client.post(
            '/accounts/citizen/register/',
            {
                'username': 'newcitizen',
                'email': 'newcitizen@example.com',
                'password1': 'Safe-test-password-2026',
                'password2': 'Safe-test-password-2026',
            },
        )

        self.assertRedirects(response, '/accounts/login/')
        user = get_user_model().objects.get(username='newcitizen')
        self.assertEqual(user.profile.role, UserProfile.Role.CITIZEN)

    def test_officer_can_sign_in_only_through_officer_page(self):
        officer = get_user_model().objects.create_user(
            username='officer',
            password='test-password-123',
        )
        UserProfile.objects.create(user=officer, role=UserProfile.Role.OFFICER)

        response = self.client.post(
            '/accounts/officer/login/',
            {'username': 'officer', 'password': 'test-password-123'},
        )
        self.assertRedirects(response, '/')
        self.assertEqual(self.client.session['_auth_user_id'], str(officer.pk))

        self.client.post('/accounts/logout/')
        wrong_portal_response = self.client.post(
            '/accounts/login/',
            {'username': 'officer', 'password': 'test-password-123'},
        )
        self.assertEqual(wrong_portal_response.status_code, 200)
        self.assertContains(wrong_portal_response, 'correct sign-in page')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_credentials_do_not_sign_user_in(self):
        response = self.client.post(
            '/accounts/login/',
            {'username': 'citizen', 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'correct username and password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_user_can_sign_out(self):
        self.client.force_login(self.user)
        response = self.client.post('/accounts/logout/')

        self.assertRedirects(response, '/accounts/login/')
        self.assertNotIn('_auth_user_id', self.client.session)

# Create your tests here.
