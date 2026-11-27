from django.core.management.base import BaseCommand

from core.models import KENYAN_COUNTIES, Project


class Command(BaseCommand):
    help = 'Add one clearly labelled demonstration project for each Kenyan county.'

    def handle(self, *args, **options):
        created_count = 0
        sample_description = (
            'This is fictional demonstration data for testing the CitizenVoice KE '
            'project catalog. It does not describe an actual funded or active '
            'government project. Replace it with verified information before '
            'using this system for real public reporting.'
        )

        for county in KENYAN_COUNTIES:
            title = f'Sample Community Project - {county}'
            _, created = Project.objects.get_or_create(
                title=title,
                county=county,
                defaults={
                    'location': 'Sample location',
                    'implementing_agency': 'Demonstration data only',
                    'description': sample_description,
                    'status': Project.Status.PLANNED,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Added {created_count} sample project(s); '
                f'{len(KENYAN_COUNTIES)} counties are covered.'
            )
        )
