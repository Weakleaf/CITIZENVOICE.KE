import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils.html import escape

from .models import KENYAN_COUNTIES, Project, ProjectReport, UserProfile


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


class ProjectReportTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.project = Project.objects.create(
            title='Sample Water Project',
            county='Nakuru',
            description='Demonstration project for reports.',
        )
        user_model = get_user_model()
        self.citizen = user_model.objects.create_user(
            username='reporter',
            password='test-password-123',
        )
        self.other_citizen = user_model.objects.create_user(
            username='otherreporter',
            password='test-password-123',
        )
        self.officer = user_model.objects.create_user(
            username='reviewofficer',
            password='test-password-123',
        )
        UserProfile.objects.create(
            user=self.officer,
            role=UserProfile.Role.OFFICER,
        )

    def make_report(self, submitter):
        return ProjectReport.objects.create(
            project=self.project,
            submitted_by=submitter,
            title='Work has stopped',
            category=ProjectReport.Category.INACTIVE,
            description='No work has been visible for several weeks.',
        )

    def test_citizen_can_submit_report_and_download_their_evidence(self):
        self.client.force_login(self.citizen)
        response = self.client.post(
            reverse('report_create'),
            {
                'project': self.project.pk,
                'title': 'Work has stopped',
                'category': ProjectReport.Category.INACTIVE,
                'description': 'No work has been visible for several weeks.',
                'evidence': SimpleUploadedFile(
                    'site-photo.png',
                    b'\x89PNG\r\n\x1a\nsample image data',
                    content_type='image/png',
                ),
            },
        )

        report = ProjectReport.objects.get(title='Work has stopped')
        self.assertRedirects(
            response,
            reverse('report_detail', args=(report.pk,)),
        )
        self.assertEqual(report.submitted_by, self.citizen)
        self.assertEqual(report.status, ProjectReport.Status.SUBMITTED)

        download_response = self.client.get(
            reverse('report_evidence_download', args=(report.pk,)),
        )
        self.assertEqual(download_response.status_code, 200)
        self.assertIn('attachment', download_response['Content-Disposition'])
        self.assertEqual(
            b''.join(download_response.streaming_content),
            b'\x89PNG\r\n\x1a\nsample image data',
        )
        download_response.close()

    def test_evidence_rejects_unsupported_and_mismatched_files(self):
        self.client.force_login(self.citizen)
        report_data = {
            'project': self.project.pk,
            'title': 'Unsafe attachment',
            'category': ProjectReport.Category.OTHER,
            'description': 'Testing evidence validation.',
        }

        unsupported_response = self.client.post(
            reverse('report_create'),
            {
                **report_data,
                'evidence': SimpleUploadedFile(
                    'notes.txt',
                    b'not an accepted evidence format',
                    content_type='text/plain',
                ),
            },
        )
        self.assertEqual(unsupported_response.status_code, 200)
        self.assertContains(unsupported_response, 'JPG, PNG, WEBP, or PDF')
        self.assertFalse(
            ProjectReport.objects.filter(title='Unsafe attachment').exists(),
        )

        mismatch_response = self.client.post(
            reverse('report_create'),
            {
                **report_data,
                'evidence': SimpleUploadedFile(
                    'fake.pdf',
                    b'this is not a PDF',
                    content_type='application/pdf',
                ),
            },
        )
        self.assertEqual(mismatch_response.status_code, 200)
        self.assertContains(mismatch_response, 'do not match')

    def test_evidence_larger_than_five_megabytes_is_rejected(self):
        self.client.force_login(self.citizen)
        response = self.client.post(
            reverse('report_create'),
            {
                'project': self.project.pk,
                'title': 'Large attachment',
                'category': ProjectReport.Category.OTHER,
                'description': 'Testing the upload size limit.',
                'evidence': SimpleUploadedFile(
                    'large-photo.jpg',
                    b'\xff\xd8\xff' + b'x' * (5 * 1024 * 1024),
                    content_type='image/jpeg',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '5 MB or smaller')
        self.assertFalse(
            ProjectReport.objects.filter(title='Large attachment').exists(),
        )

    def test_citizens_only_see_and_download_their_own_reports(self):
        own_report = self.make_report(self.citizen)
        other_report = self.make_report(self.other_citizen)
        own_report.evidence = SimpleUploadedFile(
            'private-evidence.png',
            b'\x89PNG\r\n\x1a\nprivate evidence',
            content_type='image/png',
        )
        own_report.save()
        self.client.force_login(self.citizen)

        list_response = self.client.get(reverse('report_list'))
        self.assertContains(list_response, reverse('report_detail', args=(own_report.pk,)))
        self.assertNotContains(
            list_response,
            reverse('report_detail', args=(other_report.pk,)),
        )
        self.assertEqual(
            self.client.get(
                reverse('report_detail', args=(other_report.pk,)),
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse('report_review', args=(own_report.pk,)),
            ).status_code,
            403,
        )
        download_response = self.client.get(
            reverse('report_evidence_download', args=(own_report.pk,)),
        )
        self.assertEqual(download_response.status_code, 200)
        download_response.close()
        self.client.force_login(self.other_citizen)
        self.assertEqual(
            self.client.get(
                reverse('report_evidence_download', args=(own_report.pk,)),
            ).status_code,
            403,
        )

    def test_officer_can_update_status_and_respond(self):
        report = self.make_report(self.citizen)
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse('report_review', args=(report.pk,)),
            {
                'status': ProjectReport.Status.UNDER_REVIEW,
                'officer_response': 'The concern is being reviewed.',
            },
        )

        self.assertRedirects(
            response,
            reverse('report_detail', args=(report.pk,)),
        )
        report.refresh_from_db()
        self.assertEqual(report.status, ProjectReport.Status.UNDER_REVIEW)
        self.assertEqual(
            report.officer_response,
            'The concern is being reviewed.',
        )
        self.client.force_login(self.citizen)
        citizen_detail = self.client.get(
            reverse('report_detail', args=(report.pk,)),
        )
        self.assertContains(citizen_detail, 'The concern is being reviewed.')

# Create your tests here.
