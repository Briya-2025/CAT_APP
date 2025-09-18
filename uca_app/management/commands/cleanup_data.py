from django.core.management.base import BaseCommand
from uca_app.models import Section, Assessment, GradeDistribution, CourseReport, ProjectFile

class Command(BaseCommand):
    help = 'Remove all course sections, students, assessments, and related data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete ALL sections, assessments, grade distributions, '
                    'reports, and project files from the database.\n'
                    'Use --confirm flag to proceed.'
                )
            )
            return

        # Count records before deletion
        sections_count = Section.objects.count()
        assessments_count = Assessment.objects.count()
        grade_distributions_count = GradeDistribution.objects.count()
        reports_count = CourseReport.objects.count()
        project_files_count = ProjectFile.objects.count()

        self.stdout.write(f'Found {sections_count} sections')
        self.stdout.write(f'Found {assessments_count} assessments')
        self.stdout.write(f'Found {grade_distributions_count} grade distributions')
        self.stdout.write(f'Found {reports_count} reports')
        self.stdout.write(f'Found {project_files_count} project files')

        # Delete in order to respect foreign key constraints
        self.stdout.write('Deleting grade distributions...')
        GradeDistribution.objects.all().delete()

        self.stdout.write('Deleting assessments...')
        Assessment.objects.all().delete()

        self.stdout.write('Deleting sections...')
        Section.objects.all().delete()

        self.stdout.write('Deleting reports...')
        CourseReport.objects.all().delete()

        self.stdout.write('Deleting project files...')
        ProjectFile.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully cleaned up all section and student data from the database!'
            )
        )
