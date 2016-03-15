# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('postgrest', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL([
            ("GRANT SELECT ON {} TO {};".format("registers_location, registers_costcentre, registers_itsystem", settings.POSTGREST_ROLE), None),
        ])
    ]
