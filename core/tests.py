from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from .models import KENYAN_COUNTIES, Project, UserProfile


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='citizen',
            password='test-password-123',
        )

    def test_portal_offers_each_sign_in_page(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('login'))
        self.assertContains(response, reverse('officer_login'))
        self.assertContains(response, reverse('admin:login'))
        self.assertContains(response, reverse('citizen_register'))

    def test_dashboard_redirects_to_portal_when_signed_out(self):
        response = self.client.get('/dashboard/')

        self.assertRedirects(response, '/?next=/dashboard/')

    def test_user_can_sign_in_and_open_dashboard(self):
        response = self.client.post(
            '/accounts/login/',
            {'username': 'citizen', 'password': 'test-password-123'},
        )

        self.assertRedirects(response, '/dashboard/')
        dashboard_response = self.client.get('/dashboard/')
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
        self.assertRedirects(response, '/dashboard/')
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

        self.assertRedirects(response, '/')
        self.assertNotIn('_auth_user_id', self.client.session)


class ProjectCatalogTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title='Community Health Centre',
            county='Nakuru',
            location='Nakuru Town',
            implementing_agency='County Government',
            description='Construction of a community health centre.',
            status=Project.Status.IN_PROGRESS,
        )
        self.citizen = get_user_model().objects.create_user(
            username='resident',
            password='test-password-123',
        )
        self.officer = get_user_model().objects.create_user(
            username='projectofficer',
            password='test-password-123',
        )
        UserProfile.objects.create(
            user=self.officer,
            role=UserProfile.Role.OFFICER,
        )

    def test_public_can_browse_and_view_project_details(self):
        list_response = self.client.get(reverse('project_list'))
        detail_response = self.client.get(
            reverse('project_detail', args=(self.project.pk,)),
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Community Health Centre')
        self.assertContains(list_response, 'Nakuru')
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Construction of a community health centre.')

    def test_project_list_can_filter_by_title_and_county(self):
        response = self.client.get(
            reverse('project_list'),
            {'q': 'health', 'county': 'Nakuru'},
        )
        self.assertContains(response, 'Community Health Centre')

        no_match_response = self.client.get(
            reverse('project_list'),
            {'q': 'health', 'county': 'Mombasa'},
        )
        self.assertContains(no_match_response, 'No projects found')

    def test_county_filter_lists_every_kenyan_county(self):
        response = self.client.get(reverse('project_list'))

        self.assertEqual(len(response.context['counties']), 47)
        for county in KENYAN_COUNTIES:
            self.assertContains(response, f'value="{escape(county)}"')

    def test_citizens_cannot_create_or_edit_projects(self):
        self.client.force_login(self.citizen)
        create_response = self.client.get(reverse('project_create'))
        edit_response = self.client.get(
            reverse('project_update', args=(self.project.pk,)),
        )

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)

    def test_officer_can_create_project_and_invalid_dates_are_rejected(self):
        self.client.force_login(self.officer)
        create_url = reverse('project_create')
        valid_data = {
            'title': 'Rural Access Road',
            'county': 'Kisumu',
            'location': 'West Kisumu',
            'implementing_agency': 'County Government',
            'description': 'Improvement of a rural access road.',
            'status': Project.Status.PLANNED,
            'start_date': '2026-12-01',
            'expected_completion': '2027-06-30',
        }

        response = self.client.post(create_url, valid_data)
        created_project = Project.objects.get(title='Rural Access Road')
        self.assertRedirects(
            response,
            reverse('project_detail', args=(created_project.pk,)),
        )

        invalid_data = dict(valid_data)
        invalid_data['title'] = 'Invalid Date Project'
        invalid_data['start_date'] = '2027-06-30'
        invalid_data['expected_completion'] = '2026-12-01'
        invalid_response = self.client.post(create_url, invalid_data)

        self.assertEqual(invalid_response.status_code, 200)
        self.assertContains(invalid_response, 'on or after the start date')
        self.assertFalse(
            Project.objects.filter(title='Invalid Date Project').exists(),
        )


class SampleProjectCommandTests(TestCase):
    def test_command_seeds_a_demo_project_in_each_county_once(self):
        call_command('seed_sample_projects', verbosity=0)

        self.assertEqual(Project.objects.count(), len(KENYAN_COUNTIES))
        self.assertEqual(
            set(Project.objects.values_list('county', flat=True)),
            set(KENYAN_COUNTIES),
        )
        self.assertTrue(
            all(
                'fictional demonstration data' in description
                for description in Project.objects.values_list(
                    'description',
                    flat=True,
                )
            )
        )

        call_command('seed_sample_projects', verbosity=0)
        self.assertEqual(Project.objects.count(), len(KENYAN_COUNTIES))

# Create your tests here.
