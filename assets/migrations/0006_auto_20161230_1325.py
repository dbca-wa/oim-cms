# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-12-30 05:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0005_hardwareassetextra_vtd_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicledetails',
            name='vehicle_id',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
    ]
