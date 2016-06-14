from django.core.management.base import BaseCommand
from tracking.utils_freshdesk import freshdesk_sync_contacts

class Command(BaseCommand):
    help = 'Pushes DepartmentUser data to Freshdesk\'s user system'

    def handle(self, *args, **options):
        freshdesk_sync_contacts()
