"""
WSGI config for oim_cms project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""
import confy
from django.core.wsgi import get_wsgi_application
import os

confy.read_environment_file(".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oim_cms.settings")
application = get_wsgi_application()
