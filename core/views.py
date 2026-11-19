from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import (
    CitizenAuthenticationForm,
    CitizenRegistrationForm,
    OfficerAuthenticationForm,
)
from .models import UserProfile, get_user_role


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
