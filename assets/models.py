from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from organisation.models import DepartmentUser, Location
from tracking.models import CommonFields
from datetime import datetime    


@python_2_unicode_compatible
class Vendor(models.Model):
    """Represents the vendor of a product (software, hardware or service).
    """
    name = models.CharField(
        max_length=256, unique=True, help_text='E.g. Dell, Cisco, etc.')
    details = models.TextField(null=True, blank=True)
    account_rep = models.CharField(max_length=200, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    extra_data = JSONField(default=dict, null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Suppliers(models.Model):
    """Represents a list of suppliers per asset model
    """
    STATE_CHOICES = (
			('N/A','N/A'),
            ('ACT','ACT'),
            ('NSW','NSW'),
            ('NT','NT'),
            ('QLD','QLD'),
            ('VIC','VIC'),
            ('TAS','TAS'),
            ('SA','SA'),
            ('WA','WA')
    )


    name = models.CharField(max_length=255, unique=True)
    address1 = models.CharField(max_length=255, unique=False,null=True)
    address2 = models.CharField(max_length=255, unique=False, null=True)
    address3 = models.CharField(max_length=255, unique=False, null=True)
    suburb = models.CharField(max_length=255, unique=False, null=True)
    postcode = models.CharField(max_length=255, unique=False, null=True)
    state = models.CharField(max_length=5,null=True,choices=STATE_CHOICES,default='N/A')
    effective_from = models.DateField(null=True)
    effective_to = models.DateField(null=True)
    date_modified = models.DateField(default=datetime.now, blank=True)
    date_created = models.DateTimeField(default=datetime.now, blank=True)


    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Invoice(CommonFields):
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    vendor_ref = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="The vendor's reference or invoice number for this order.")
    job_number = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='The P&W job number relating to this order.')
    date = models.DateField(
        blank=True, null=True, help_text='The date shown on the invoice.')
    etj_number = models.CharField(
        max_length=20, null=True, blank=True, verbose_name='ETJ number.')
    total_value = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True,
        help_text='The total value of the invoice (excluding GST).')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('-job_number',)

    def __str__(self):
        if self.vendor_ref and self.total_value:
            return '{} {} - {:.2f}'.format(self.vendor.name, self.vendor_ref, self.total_value)
        elif self.vendor_ref:
            return '{} - {:.2f}'.format(self.vendor.name, self.total_value)
        else:
            return self.vendor.name


class Asset(CommonFields):
    """Abstract model class to represent fields common to all asset types.
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    date_purchased = models.DateField(null=True, blank=True)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, blank=True, null=True)
    purchased_value = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True,
        help_text='The amount paid for this asset, inclusive of any upgrades (excluding GST).')
    notes = models.TextField(blank=True)
    supplier = models.ForeignKey(Suppliers, on_delete=models.PROTECT)
    rsid = models.IntegerField(default='0')

    class Meta:
        abstract = True


@python_2_unicode_compatible
class SoftwareLicense(CommonFields):
    """Represents a software licensing arrangement. A licence for software may
    be obtained from a separate vendor than the one that creates the software
    (e.g. a supplier of COTS software).
    """
    name = models.CharField(max_length=256, unique=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    support = models.TextField(
        blank=True, help_text='Support timeframe or scope')
    support_url = models.URLField(max_length=2000, null=True, blank=True)
    oss = models.NullBooleanField(
        default=None, help_text='Open-source/free software license?')
    primary_user = models.ForeignKey(
        DepartmentUser, on_delete=models.PROTECT, null=True, blank=True)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, null=True, blank=True)
    used_licenses = models.PositiveSmallIntegerField(default=0, editable=False)
    available_licenses = models.PositiveSmallIntegerField(
        default=0, null=True, blank=True)
    license_details = models.TextField(
        blank=True, help_text='Direct license keys or details')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class HardwareModel(models.Model):
    """Represents the vendor model type for a physical hardware asset.
    """
    TYPE_CHOICES = (
        ('Air conditioner', 'Air conditioner'),
        ('Camera - Compact', 'Camera - Compact'),
        ('Camera - SLR', 'Camera - SLR'),
        ('Camera - Security (IP)', 'Camera - Security (IP)'),
        ('Camera - Security (non-IP)', 'Camera - Security (non-IP)'),
        ('Camera - Other', 'Camera - Other'),
        ('Chassis', 'Chassis'),
        ('Computer - Desktop', 'Computer - Desktop'),
        ('Computer - Docking station', 'Computer - Docking station'),
        ('Computer - Input device', 'Computer - Input device'),
        ('Computer - Laptop', 'Computer - Laptop'),
        ('Computer - Misc Accessory', 'Computer - Misc Accessory'),
        ('Computer - Monitor', 'Computer - Monitor'),
        ('Computer - Tablet PC', 'Computer - Tablet PC'),
        ('Computer - Other', 'Computer - Other'),
        ### New Categories From FS_COM Asset Databases
        ('Comms - Airband Handheld','Comms - Airband Handheld' ),
        ('Comms - SIM - BGAN','Comms - SIM - BGAN'),
        ('Comms - Radio Over IP','Comms - Radio Over IP'),
        ('Comms - UHF','Comms - UHF'),
        ('Comms - VHF','Comms - VHF'),
        ('Comms - HF','Comms - HF'),
        ('Comms - Dual Band VH/U','Comms - Dual Band VH/U'),
        ('Comms - Satellite Phone','Comms - Satellite Phone'),
        ('Comms - SIM - Satellite Phone','Comms - SIM - Satellite Phone'),
        ('Comms - BGAN','Comms - BGAN'),
        ('Comms - rBGAN','Comms - rBGAN'),
        ('Comms - 2 Way Satellite System','Comms - 2 Way Satellite System'),
        ('Comms - Satellite System (DEC VSAT)','Comms - Satellite System (DEC VSAT)'),
        ('Comms - Automatic Weather Station','Comms - Automatic Weather Station'),
        ('Comms - Satellite Base Telephone','Comms - Satellite Base Telephone'),
        ('Comms - Telephone Interface','Comms - Telephone Interface'),
        ('Comms - FMS Cache','Comms - FMS Cache'),
        ('Comms - Communications Bus','Comms - Communications Bus'),
        ('Comms - Mobile Communication Vehicle','Comms - Mobile Communication Vehicle'),
        ('Comms - Tracking Device','Comms - Tracking Device'),
        ('Comms - Explorer PTT Terminal','Comms - Explorer PTT Terminal'),
        ('Comms - Codan Portable Repeater','Comms - Codan Portable Repeater'),
        ('Comms - VHF (Digital)','Comms - VHF (Digital)'),
        ###########################################
        ('Environmental monitor', 'Environmental monitor'),
        ('Network - Hub', 'Network - Hub'),
        ('Network - Media converter', 'Network - Media converter'),
        ('Network - Modem', 'Network - Modem'),
        ('Network - Module or card', 'Network - Module or card'),
        ('Network - Power injector', 'Network - Power injector'),
        ('Network - Router', 'Network - Router'),
        ('Network - Switch (Ethernet)', 'Network - Switch (Ethernet)'),
        ('Network - Switch (FC)', 'Network - Switch (FC)'),
        ('Network - Wireless AP', 'Network - Wireless AP'),
        ('Network - Wireless bridge', 'Network - Wireless bridge'),
        ('Network - Wireless controller', 'Network - Wireless controller'),
        ('Network - Other', 'Network - Other'),
        ('Phone - Conference', 'Phone - Conference'),
        ('Phone - Desk', 'Phone - Desk'),
        ('Phone - Gateway', 'Phone - Gateway'),
        ('Phone - Mobile', 'Phone - Mobile'),
        ('Phone - Wireless or portable', 'Phone - Wireless or portable'),
        ('Phone - Other', 'Phone - Other'),
        ('Power Distribution Unit', 'Power Distribution Unit'),
        ('Printer - Fax machine', 'Printer - Fax machine'),
        ('Printer - Local', 'Printer - Local'),
        ('Printer - Local Multifunction', 'Printer - Local Multifunction'),
        ('Printer - Multifunction copier', 'Printer - Multifunction copier'),
        ('Printer - Plotter', 'Printer - Plotter'),
        ('Printer - Workgroup', 'Printer - Workgroup'),
        ('Printer - Other', 'Printer - Other'),
        ('Projector', 'Projector'),
        ('Rack', 'Rack'),
        ('Server - Blade', 'Server - Blade'),
        ('Server - Rackmount', 'Server - Rackmount'),
        ('Server - Tower', 'Server - Tower'),
        ('Storage - Disk array', 'Storage - Disk array'),
        ('Storage - NAS', 'Storage - NAS'),
        ('Storage - SAN', 'Storage - SAN'),
        ('Storage - Other', 'Storage - Other'),
        ('Speaker', 'Speaker'),
        ('Tablet', 'Tablet'),
        ('Tape autoloader', 'Tape autoloader'),
        ('Tape drive', 'Tape drive'),
        ('UPS', 'UPS'),
        ('Other', 'Other'),

    )

    model_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    model_no = models.CharField(
        max_length=50,
        help_text="The short model number (eg. '7945G' for a Cisco 7956G phone). Do not enter the class (eg. '7900 series') or the product code (eg. 'WS-7945G=')")
    lifecycle = models.IntegerField(
        help_text="Enter in years how long we should keep items of this model before they get decomissioned. Desktops should generally be three years, servers and networking equipment five years.")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('vendor', 'model_no')

    def __str__(self):
        return '{} {}'.format(self.vendor, self.model_no)


@python_2_unicode_compatible
class HardwareAsset(Asset):
    """Represents a physical hardware asset.
    """
    STATUS_CHOICES = (
        ('In storage', 'In storage'),
        ('Deployed', 'Deployed'),
        ('Disposed', 'Disposed'),
		('Available','Available'),
		('Decommissioned','Decommissioned'),
		('Hired','Hired'),
		('In Service','In Service'),
		('Lost','Lost'),
		('Return to Manufacturer','Return to Manufacturer'),
		('Sold','Sold'),
		('Stolen','Stolen'),
		('Location unknown','Location unknown'),
		('Invalid','Invalid')
    )

    asset_tag = models.CharField(max_length=10, unique=True)
    finance_asset_tag = models.CharField(
        max_length=10, null=True, blank=True,
        help_text='The Finance Services Branch asset number for (leave blank if unsure).')
    hardware_model = models.ForeignKey(HardwareModel, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='In storage')
    serial = models.CharField(
        max_length=50, help_text='The serial number or service tag.')
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    assigned_user = models.ForeignKey(
        DepartmentUser, on_delete=models.PROTECT, null=True, blank=True)
	
    class Meta:
        ordering = ('-asset_tag',)

    def __str__(self):
        return self.asset_tag

@python_2_unicode_compatible
class HardwareAssetExtra(models.Model):
	
	ha = models.ForeignKey(HardwareAsset, on_delete=models.PROTECT)
	voice_no = models.CharField(max_length=40, null=True, blank=True, help_text='The Telephone number of the Device')
	fax_no	= models.CharField(max_length=40, null=True, blank=True, help_text='The Fax number of the Device')
	icc_id	= models.CharField(max_length=40, null=True, blank=True, help_text='The ICC ID number')
	msisdn = models.CharField(max_length=24, null=True, blank=True)
	service_provider = models.CharField(max_length=100, null=True, blank=True, help_text='Name of Provider')
	service_plan = models.CharField(max_length=100, null=True, blank=True, help_text='Name of Provider Plan')
	sim_pin = models.CharField(max_length=10, null=True, blank=True)
	account_number = models.CharField(max_length=100, null=True, blank=True)
	account_pin = models.CharField(max_length=10, null=True, blank=True)
	date_modified = models.DateField(default=datetime.now)
	date_created = models.DateTimeField(default=datetime.now)
	comms_type = models.CharField(max_length=100)
	vtd_id = models.IntegerField(null=True, blank=True)
	vehicle_id = models.IntegerField(null=True, blank=True)
	
	def __str__(self):
		return self.asset_tag

@python_2_unicode_compatible
class VehicleDetails(models.Model):
	vehicle_id = models.IntegerField(null=True, blank=True,unique=True)
	rego = models.CharField(max_length=20, null=True, blank=True, help_text='Vehicle Registration')
	make = models.CharField(max_length=120, null=True, blank=True, help_text='Vehicle Make')
	model = models.CharField(max_length=120, null=True, blank=True, help_text='Vehicle Model')
	kms = models.IntegerField(null=True, blank=True)
	light_flag = models.NullBooleanField(default=None)
	category = models.CharField(max_length=170, null=True, blank=True, help_text='Category')
	rate = models.IntegerField(null=True, blank=True)
	default_job_id = models.CharField(max_length=40, null=True, blank=True, help_text='JOB ID')
	month_cost = models.IntegerField(null=True, blank=True)
	status_flag = models.CharField(max_length=2, null=True, blank=True)
	cost_centre = models.CharField(max_length=20, null=True, blank=True)
	manufactured_month_year = models.DateField(null=True, blank=True)
	engine_no = models.CharField(max_length=40, null=True, blank=True)
	diesel_engine = models.NullBooleanField(default=None)
	automatic_engine = models.NullBooleanField(default=None)
	tare = models.IntegerField(null=True, blank=True)
	gcm = models.IntegerField(null=True, blank=True)
	serial_chassis_no = models.CharField(max_length=60, null=True, blank=True)
	date_deleted = models.DateField(null=True, blank=True)
	comments = models.CharField(max_length=120, null=True, blank=True)
	comments2 = models.CharField(max_length=120, null=True, blank=True)
	comments3 = models.CharField(max_length=120, null=True, blank=True)
	location = models.CharField(max_length=120, null=True, blank=True)

	def __str__(self):
		return self.make

