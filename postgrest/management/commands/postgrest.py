from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import subprocess
from confy import env

class Command(BaseCommand):
    help = 'Launches postgrest api backend'

    def handle(self, *args, **options):
        subprocess.check_call([settings.POSTGREST_BINARY, env("DATABASE_URL").replace("postgis", "postgres"), "-a", settings.POSTGREST_ROLE, "-p", str(env("POSTGREST_PORT"))])
