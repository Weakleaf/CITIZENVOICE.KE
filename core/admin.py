from django.contrib import admin

from .models import Project, ProjectReport, UserProfile


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


@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'submitted_by', 'status', 'created_at')
    list_filter = ('status', 'category', 'project__county')
    search_fields = ('title', 'project__title', 'submitted_by__username')
    readonly_fields = ('created_at', 'updated_at')
