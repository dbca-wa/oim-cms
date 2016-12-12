# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-12-12 07:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registers', '0010_auto_20161212_1504'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itsystemhardware',
            options={'ordering': ('computer__hostname',), 'verbose_name_plural': 'IT System hardware'},
        ),
        migrations.RemoveField(
            model_name='backup',
            name='parent_host',
        ),
        migrations.RemoveField(
            model_name='backup',
            name='system',
        ),
        migrations.AlterUniqueTogether(
            name='itsystemhardware',
            unique_together=set([('computer', 'role')]),
        ),
    ]
