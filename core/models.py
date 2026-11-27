from django.conf import settings
from django.db import models


KENYAN_COUNTIES = (
    'Mombasa',
    'Kwale',
    'Kilifi',
    'Tana River',
    'Lamu',
    'Taita Taveta',
    'Garissa',
    'Wajir',
    'Mandera',
    'Marsabit',
    'Isiolo',
    'Meru',
    'Tharaka-Nithi',
    'Embu',
    'Kitui',
    'Machakos',
    'Makueni',
    'Nyandarua',
    'Nyeri',
    'Kirinyaga',
    "Murang'a",
    'Kiambu',
    'Turkana',
    'West Pokot',
    'Samburu',
    'Trans Nzoia',
    'Uasin Gishu',
    'Elgeyo-Marakwet',
    'Nandi',
    'Baringo',
    'Laikipia',
    'Nakuru',
    'Narok',
    'Kajiado',
    'Kericho',
    'Bomet',
    'Kakamega',
    'Vihiga',
    'Bungoma',
    'Busia',
    'Siaya',
    'Kisumu',
    'Homa Bay',
    'Migori',
    'Kisii',
    'Nyamira',
    'Nairobi City',
)


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


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETED = 'completed', 'Completed'
        ON_HOLD = 'on_hold', 'On hold'

    title = models.CharField(max_length=200)
    county = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)
    implementing_agency = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    start_date = models.DateField(null=True, blank=True)
    expected_completion = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('county', 'title')

    def __str__(self):
        return f'{self.title} ({self.county})'


def get_user_role(user):
    if user.is_superuser:
        return 'admin'

    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        return UserProfile.Role.CITIZEN
