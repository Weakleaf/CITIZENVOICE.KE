from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CITIZEN = 'citizen', 'Citizen'
        OFFICER = 'officer', 'Project officer'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CITIZEN,
    )

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


def get_user_role(user):
    if user.is_superuser:
        return 'admin'

    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        return UserProfile.Role.CITIZEN
