# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-22 03:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0004_auto_20170918_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='computer',
            name='os_arch',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='OS architecture'),
        ),
        migrations.AlterField(
            model_name='computer',
            name='os_name',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='OS name'),
        ),
        migrations.AlterField(
            model_name='computer',
            name='os_service_pack',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='OS service pack'),
        ),
        migrations.AlterField(
            model_name='computer',
            name='os_version',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='OS version'),
        ),
    ]