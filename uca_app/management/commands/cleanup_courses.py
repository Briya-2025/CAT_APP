from django.core.management.base import BaseCommand
from uca_app.models import Course, CourseConfiguration

class Command(BaseCommand):
    help = 'Remove all courses and course configurations from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all courses',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete ALL courses and course configurations from the database.\n'
                    'Use --confirm flag to proceed.'
                )
            )
            return

        # Count records before deletion
        courses_count = Course.objects.count()
        configs_count = CourseConfiguration.objects.count()

        self.stdout.write(f'Found {courses_count} courses')
        self.stdout.write(f'Found {configs_count} course configurations')

        # Delete course configurations first (they have foreign key to courses)
        self.stdout.write('Deleting course configurations...')
        CourseConfiguration.objects.all().delete()

        # Then delete courses
        self.stdout.write('Deleting courses...')
        Course.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully cleaned up all courses from the database!'
            )
        )
