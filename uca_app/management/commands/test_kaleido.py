from django.core.management.base import BaseCommand
from uca_app.views import test_kaleido_functionality

class Command(BaseCommand):
    help = 'Test Kaleido functionality'

    def handle(self, *args, **options):
        self.stdout.write("Testing Kaleido functionality...")
        
        if test_kaleido_functionality():
            self.stdout.write(
                self.style.SUCCESS('✅ Kaleido is working properly!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Kaleido is not working properly!')
            )
