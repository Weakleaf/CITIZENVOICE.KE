from django.contrib import admin

from .models import Project, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'county', 'status', 'updated_at')
    list_filter = ('county', 'status')
    search_fields = ('title', 'county', 'location', 'implementing_agency')
