from functools import wraps
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CitizenAuthenticationForm,
    CitizenRegistrationForm,
    OfficerAuthenticationForm,
)
from .models import (
    KENYAN_COUNTIES,
    Project,
    ProjectReport,
    UserProfile,
    get_user_role,
)
from .project_forms import ProjectForm
from .report_forms import ProjectReportForm, ProjectReportReviewForm


def portal(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/portal.html')


def can_manage_projects(user):
    return (
        user.is_authenticated
        and get_user_role(user) in ('officer', 'admin')
    )


def project_manager_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not can_manage_projects(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped_view


def citizen_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if get_user_role(request.user) != UserProfile.Role.CITIZEN:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped_view


class CitizenLoginView(auth_views.LoginView):
    template_name = 'core/login.html'
    authentication_form = CitizenAuthenticationForm
    extra_context = {
        'page_title': 'Citizen sign in',
        'heading': 'Citizen sign in',
        'intro': 'Sign in to follow public projects and participate in your community.',
        'switch_url': 'officer_login',
        'switch_text': 'Are you a project officer? Sign in here.',
        'register_url': 'citizen_register',
    }


class OfficerLoginView(auth_views.LoginView):
    template_name = 'core/login.html'
    authentication_form = OfficerAuthenticationForm
    extra_context = {
        'page_title': 'Officer sign in',
        'heading': 'Project officer sign in',
        'intro': 'Sign in to manage project information and respond to citizen reports.',
        'switch_url': 'login',
        'switch_text': 'Are you a citizen? Sign in here.',
    }


@transaction.atomic
def citizen_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role=UserProfile.Role.CITIZEN)
            messages.success(request, 'Your citizen account has been created. Please sign in.')
            return redirect('login')
    else:
        form = CitizenRegistrationForm()

    return render(request, 'core/login.html', {
        'form': form,
        'page_title': 'Create a citizen account',
        'heading': 'Create your citizen account',
        'intro': 'Register to follow public projects and participate in your community.',
        'submit_label': 'Create account',
        'switch_url': 'login',
        'switch_text': 'Already registered? Sign in.',
    })


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html', {
        'account_status': 'Active',
        'account_type': {
            'citizen': 'Citizen',
            'officer': 'Project officer',
            'admin': 'System administrator',
        }[get_user_role(request.user)],
    })


def project_list(request):
    projects = Project.objects.all()
    query = request.GET.get('q', '').strip()
    county = request.GET.get('county', '').strip()

    if query:
        projects = projects.filter(title__icontains=query)
    if county:
        projects = projects.filter(county__iexact=county)

    return render(request, 'core/project_list.html', {
        'projects': projects,
        'counties': KENYAN_COUNTIES,
        'query': query,
        'selected_county': county,
        'can_manage_projects': can_manage_projects(request.user),
    })


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'core/project_detail.html', {
        'project': project,
        'can_manage_projects': can_manage_projects(request.user),
        'can_submit_reports': (
            request.user.is_authenticated
            and get_user_role(request.user) == UserProfile.Role.CITIZEN
        ),
    })


@project_manager_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, 'Project created successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, 'core/project_form.html', {
        'form': form,
        'heading': 'Add a public project',
        'submit_label': 'Create project',
    })


@project_manager_required
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, 'core/project_form.html', {
        'form': form,
        'project': project,
        'heading': 'Update project',
        'submit_label': 'Save changes',
    })


@login_required
def report_list(request):
    reports = ProjectReport.objects.select_related(
        'project',
        'submitted_by',
    )
    if not can_manage_projects(request.user):
        reports = reports.filter(submitted_by=request.user)

    return render(request, 'core/report_list.html', {
        'reports': reports,
        'can_manage_projects': can_manage_projects(request.user),
    })


@citizen_required
def report_create(request):
    initial = {}
    project_id = request.GET.get('project')
    if request.method != 'POST' and project_id:
        initial['project'] = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        form = ProjectReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.submitted_by = request.user
            report.save()
            messages.success(request, 'Your project report has been submitted.')
            return redirect('report_detail', pk=report.pk)
    else:
        form = ProjectReportForm(initial=initial)

    return render(request, 'core/report_form.html', {
        'form': form,
    })


@login_required
def report_detail(request, pk):
    report = get_object_or_404(
        ProjectReport.objects.select_related('project', 'submitted_by'),
        pk=pk,
    )
    can_manage = can_manage_projects(request.user)
    if not can_manage and report.submitted_by_id != request.user.pk:
        raise PermissionDenied

    return render(request, 'core/report_detail.html', {
        'report': report,
        'can_manage_projects': can_manage,
    })


@project_manager_required
def report_review(request, pk):
    report = get_object_or_404(
        ProjectReport.objects.select_related('project', 'submitted_by'),
        pk=pk,
    )
    if request.method == 'POST':
        form = ProjectReportReviewForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'The report review has been updated.')
            return redirect('report_detail', pk=report.pk)
    else:
        form = ProjectReportReviewForm(instance=report)

    return render(request, 'core/report_review.html', {
        'form': form,
        'report': report,
    })


@login_required
def report_evidence_download(request, pk):
    report = get_object_or_404(
        ProjectReport.objects.select_related('submitted_by'),
        pk=pk,
    )
    can_manage = can_manage_projects(request.user)
    if not can_manage and report.submitted_by_id != request.user.pk:
        raise PermissionDenied
    if not report.evidence:
        raise PermissionDenied

    return FileResponse(
        report.evidence.open('rb'),
        as_attachment=True,
        filename=Path(report.evidence.name).name,
    )
