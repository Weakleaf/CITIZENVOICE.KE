from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.portal, name='portal'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/new/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path(
        'projects/<int:pk>/edit/',
        views.project_update,
        name='project_update',
    ),
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
