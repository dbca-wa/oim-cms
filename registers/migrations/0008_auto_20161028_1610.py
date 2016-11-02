# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-28 08:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registers', '0007_auto_20161025_1206'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentapproval',
            name='department_user',
        ),
        migrations.RemoveField(
            model_name='itsystem',
            name='contingency_plan_approvals',
        ),
        migrations.AlterField(
            model_name='itsystem',
            name='contingency_plan',
            field=models.FileField(blank=True, max_length=255, null=True, upload_to='uploads/%Y/%m/%d'),
        ),
        migrations.DeleteModel(
            name='DocumentApproval',
        ),
    ]