from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/login/', views.CitizenLoginView.as_view(), name='login'),
    path(
        'accounts/citizen/login/',
        views.CitizenLoginView.as_view(),
        name='citizen_login',
    ),
    path(
        'accounts/officer/login/',
        views.OfficerLoginView.as_view(),
        name='officer_login',
    ),
    path(
        'accounts/citizen/register/',
        views.citizen_register,
        name='citizen_register',
    ),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]
