# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-02 02:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisation', '0014_auto_20170630_0850'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentuser',
            name='employee_id',
            field=models.CharField(blank=True, help_text='HR Employee ID. Enter n/a if no ID provided', max_length=128, null=True, unique=True, verbose_name='Employee ID'),
        ),
    ]
