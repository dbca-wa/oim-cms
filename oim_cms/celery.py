from __future__ import absolute_import
from celery import Celery
import confy

confy.read_environment_file('.env')

app = Celery('oim_cms')
app.config_from_object('django.conf:settings')
# Don't use autodiscover for tasks; define CELERY_IMPORTS in settings.
#app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
