# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-10-19 06:34
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organisation', '0002_departmentuser_extension'),
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HardwareAsset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('extra_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('date_purchased', models.DateField(blank=True, null=True)),
                ('purchased_value', models.DecimalField(blank=True, decimal_places=2, help_text='The amount paid for this asset, inclusive of any upgrades (excluding GST).', max_digits=20, null=True)),
                ('notes', models.TextField(blank=True)),
                ('asset_tag', models.CharField(max_length=10, unique=True)),
                ('finance_asset_tag', models.CharField(blank=True, help_text='The Finance Services Branch asset number for (leave blank if unsure).', max_length=10, null=True)),
                ('status', models.CharField(choices=[('In storage', 'In storage'), ('Deployed', 'Deployed'), ('Disposed', 'Disposed')], default='In storage', max_length=50)),
                ('serial', models.CharField(help_text='The serial number or service tag.', max_length=50)),
                ('assigned_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organisation.DepartmentUser')),
                ('cost_centre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organisation.CostCentre')),
            ],
            options={
                'ordering': ('-asset_tag',),
            },
        ),
        migrations.CreateModel(
            name='HardwareModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_type', models.CharField(choices=[('Air conditioner', 'Air conditioner'), ('Camera - Compact', 'Camera - Compact'), ('Camera - SLR', 'Camera - SLR'), ('Camera - Security (IP)', 'Camera - Security (IP)'), ('Camera - Security (non-IP)', 'Camera - Security (non-IP)'), ('Camera - Other', 'Camera - Other'), ('Chassis', 'Chassis'), ('Computer - Desktop', 'Computer - Desktop'), ('Computer - Docking station', 'Computer - Docking station'), ('Computer - Input device', 'Computer - Input device'), ('Computer - Laptop', 'Computer - Laptop'), ('Computer - Misc Accessory', 'Computer - Misc Accessory'), ('Computer - Monitor', 'Computer - Monitor'), ('Computer - Tablet PC', 'Computer - Tablet PC'), ('Computer - Other', 'Computer - Other'), ('Environmental monitor', 'Environmental monitor'), ('Network - Hub', 'Network - Hub'), ('Network - Media converter', 'Network - Media converter'), ('Network - Modem', 'Network - Modem'), ('Network - Module or card', 'Network - Module or card'), ('Network - Power injector', 'Network - Power injector'), ('Network - Router', 'Network - Router'), ('Network - Switch (Ethernet)', 'Network - Switch (Ethernet)'), ('Network - Switch (FC)', 'Network - Switch (FC)'), ('Network - Wireless AP', 'Network - Wireless AP'), ('Network - Wireless bridge', 'Network - Wireless bridge'), ('Network - Wireless controller', 'Network - Wireless controller'), ('Network - Other', 'Network - Other'), ('Phone - Conference', 'Phone - Conference'), ('Phone - Desk', 'Phone - Desk'), ('Phone - Gateway', 'Phone - Gateway'), ('Phone - Mobile', 'Phone - Mobile'), ('Phone - Wireless or portable', 'Phone - Wireless or portable'), ('Phone - Other', 'Phone - Other'), ('Power Distribution Unit', 'Power Distribution Unit'), ('Printer - Fax machine', 'Printer - Fax machine'), ('Printer - Local', 'Printer - Local'), ('Printer - Local Multifunction', 'Printer - Local Multifunction'), ('Printer - Multifunction copier', 'Printer - Multifunction copier'), ('Printer - Plotter', 'Printer - Plotter'), ('Printer - Workgroup', 'Printer - Workgroup'), ('Printer - Other', 'Printer - Other'), ('Projector', 'Projector'), ('Rack', 'Rack'), ('Server - Blade', 'Server - Blade'), ('Server - Rackmount', 'Server - Rackmount'), ('Server - Tower', 'Server - Tower'), ('Storage - Disk array', 'Storage - Disk array'), ('Storage - NAS', 'Storage - NAS'), ('Storage - SAN', 'Storage - SAN'), ('Storage - Other', 'Storage - Other'), ('Speaker', 'Speaker'), ('Tablet', 'Tablet'), ('Tape autoloader', 'Tape autoloader'), ('Tape drive', 'Tape drive'), ('UPS', 'UPS'), ('Other', 'Other')], max_length=50)),
                ('model_no', models.CharField(help_text="The short model number (eg. '7945G' for a Cisco 7956G phone). Do not enter the class (eg. '7900 series') or the product code (eg. 'WS-7945G=')", max_length=50)),
                ('lifecycle', models.IntegerField(help_text='Enter in years how long we should keep items of this model before they get decomissioned. Desktops should generally be three years, servers and networking equipment five years.')),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('vendor', 'model_no'),
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('extra_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('vendor_ref', models.CharField(blank=True, help_text="The vendor's reference or invoice number for this order.", max_length=50, null=True)),
                ('job_number', models.CharField(blank=True, help_text='The P&W job number relating to this order.', max_length=50, null=True)),
                ('date', models.DateField(blank=True, help_text='The date shown on the invoice.', null=True)),
                ('etj_number', models.CharField(blank=True, max_length=20, null=True, verbose_name='ETJ number.')),
                ('total_value', models.DecimalField(blank=True, decimal_places=2, help_text='The total value of the invoice (excluding GST).', max_digits=20, null=True)),
                ('notes', models.TextField(blank=True)),
                ('cost_centre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organisation.CostCentre')),
                ('org_unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organisation.OrgUnit')),
            ],
            options={
                'ordering': ('-job_number',),
            },
        ),
        migrations.AddField(
            model_name='vendor',
            name='account_rep',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='website',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='details',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='extra_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='name',
            field=models.CharField(help_text='E.g. Dell, Cisco, etc.', max_length=256, unique=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assets.Vendor'),
        ),
        migrations.AddField(
            model_name='hardwaremodel',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assets.Vendor'),
        ),
        migrations.AddField(
            model_name='hardwareasset',
            name='hardware_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assets.HardwareModel'),
        ),
        migrations.AddField(
            model_name='hardwareasset',
            name='invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='assets.Invoice'),
        ),
        migrations.AddField(
            model_name='hardwareasset',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organisation.Location'),
        ),
        migrations.AddField(
            model_name='hardwareasset',
            name='org_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organisation.OrgUnit'),
        ),
        migrations.AddField(
            model_name='hardwareasset',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='assets.Vendor'),
        ),
    ]
