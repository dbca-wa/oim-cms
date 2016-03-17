from __future__ import unicode_literals, absolute_import
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.db import models

from mptt.models import MPTTModel, TreeForeignKey
from dateutil.relativedelta import relativedelta
from datetime import timedelta

from tracking import models as tracking


CRITICALITY_CHOICES = (
    (1, 'Critical'),
    (2, 'Moderate'),
    (3, 'Low'),
)


class Function(models.Model):
    SERVICE_CHOICES = (
        (1, "Service 1"),
        (2, "Service 2"),
        (3, "Service 3"),
        (4, "Service 4"),
        (5, "Service 5"),
        (6, "Service 6"),
        (7, "Service 7"),
        (8, "Service 8"),
        (9, "Common Service 9 - OIM"),
        (10, "Common Service 10 - ODG"),
        (11, "Common Service 11 - ???"),
    )
    SERVICE_CHOICES_DICT = dict(SERVICE_CHOICES)
    service = models.PositiveSmallIntegerField(choices=SERVICE_CHOICES, default=4)
    name = models.CharField(max_length=256, unique=True)

    def __str__(self):
        return self.name


class Process(models.Model):
    name = models.CharField(max_length=256, unique=True)
    function = models.ForeignKey(Function, on_delete=models.PROTECT, null=True, blank=True)
    mtd = models.DurationField(help_text="Maximum Tolerable Downtime (days hh:mm:ss)", default=timedelta(days=14))
    rto = models.DurationField(help_text="Recovery Time Objective (days hh:mm:ss)", default=timedelta(days=7))
    rpo = models.DurationField(help_text="Recovery Point Objective/Data Loss Interval (days hh:mm:ss)", default=timedelta(hours=24))
    users = models.PositiveSmallIntegerField(default=1)
    #TODO: Add validation for durationfields

    class Meta:
        verbose_name_plural = 'processes'

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=256, unique=True)
    manager = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, null=True, blank=True)
    address = models.TextField(unique=True)
    pobox = models.TextField(blank=True)
    phone = models.CharField(max_length=128, null=True, blank=True)
    fax = models.CharField(max_length=128, null=True, blank=True)
    email = models.CharField(max_length=128, null=True, blank=True)
    point = models.PointField(null=True, blank=True)
    url = models.CharField(max_length=2000, help_text="URL to webpage with more information", null=True, blank=True)
    bandwidth_url = models.CharField(max_length=2000, help_text="URL to prtg graph of bw utilisation", null=True, blank=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.address)

    def as_dict(self):
        return {k: getattr(self, k) for k in ("name", "address", "pobox", "phone", "fax", "email") if getattr(self, k)}

    def save(self, *args, **kwargs):
        for orgunit in self.orgunit_set.all():
            orgunit.save()
        super(Location, self).save(*args, **kwargs)

    class Meta:
        ordering = ('name',)


class SecondaryLocation(models.Model):
    location = models.ForeignKey(Location)
    name = models.CharField(max_length=256, unique=True)
    manager = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, null=True, blank=True)
    phone = models.CharField(max_length=128, null=True, blank=True)
    fax = models.CharField(max_length=128, null=True, blank=True)
    email = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        for orgunit in self.orgunit_set.all():
            orgunit.save()
        super(SecondaryLocation, self).save(*args, **kwargs)

    def as_dict(self):
        return {k: getattr(self, k) for k in ("name", "phone", "fax", "email") if getattr(self, k)}


class OrgUnit(MPTTModel):
    TYPE_CHOICES = (
        (0, "Department"),
        (1, "Division"),
        (2, "Branch"),
        (3, "Region"),
        (4, "Cost Centre"),
        (5, "Office"),
        (6, "District"),
        (7, "Section"),
    )
    TYPE_CHOICES_DICT = dict(TYPE_CHOICES)
    unit_type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=4)
    ad_guid = models.CharField(max_length=48, unique=True, null=True, editable=False)
    ad_dn = models.CharField(max_length=512, unique=True, null=True, editable=False)
    name = models.CharField(max_length=256, unique=True)
    acronym = models.CharField(max_length=16, null=True, blank=True)
    manager = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, null=True, blank=True)
    parent = TreeForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children', db_index=True)
    details = JSONField(null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True)
    secondary_location = models.ForeignKey(SecondaryLocation, on_delete=models.PROTECT, null=True, blank=True)

    def cc(self):
        try:
            return self.costcentre
        except:
            return None

    def __str__(self):
        name = self.name
        if self.acronym:
            name = "{} - {}".format(self.acronym, name)
        if self.cc():
            return "{} - CC{}".format(name, self.cc())
        return name

    def members(self):
        from tracking.models import DepartmentUser
        return DepartmentUser.objects.filter(org_unit__in=self.get_descendants(include_self=True), **DepartmentUser.ACTIVE_FILTER)

    def save(self, *args, **kwargs):
        self.details = self.details or {}
        self.details.update({
            "type": self.get_unit_type_display(),
        })
        if self.secondary_location:
            self.location = self.secondary_location.location
        if not getattr(self, "cheap_save", False):
            for user in self.departmentuser_set.all():
                user.save()
        super(OrgUnit, self).save(*args, **kwargs)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        ordering = ('name',)


class CostCentre(models.Model):
    name = models.CharField(max_length=25, unique=True, editable=False)
    code = models.CharField(max_length=5, unique=True)
    division = models.ForeignKey(OrgUnit, null=True, editable=False, related_name="costcentres_in_division")
    org_position = models.OneToOneField(OrgUnit, unique=True)
    manager = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, related_name="manage_ccs", null=True, blank=True)
    business_manager = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, related_name="bmanage_ccs", help_text="Business Manager", null=True, blank=True)
    admin = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, related_name="admin_ccs", help_text="Admin", null=True, blank=True)
    tech_contact = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, related_name="tech_ccs", help_text="Technical Contact", null=True, blank=True)

    def save(self, *args, **kwargs):
        self.name = str(self)
        division = self.org_position.get_ancestors(include_self=True).filter(unit_type=1)
        if division:
            self.division = division.first()
        for user in self.departmentuser_set.all():
            user.save()
        super(CostCentre, self).save(*args, **kwargs)

    def __str__(self):
        name = '{}'.format(self.code)
        dept = self.org_position.get_ancestors(include_self=True).filter(unit_type=0)
        if dept:
            name += " ({})".format(dept.first().acronym)
        return name

    class Meta:
        ordering = ('code',)


class Software(models.Model):
    """A model to represent a discrete unit of software (OS, runtime, etc.)
    """
    name = models.CharField(max_length=2048, unique=True)
    url = models.CharField(max_length=2000, null=True, blank=True)
    license = models.ForeignKey('registers.SoftwareLicense', on_delete=models.PROTECT, null=True)
    os = models.BooleanField(default=False, verbose_name='OS', help_text='Software is an operating system?')

    class Meta:
        verbose_name_plural = 'software'

    def __str__(self):
        return self.name


class Hardware(tracking.CommonFields):
    device_type = models.PositiveSmallIntegerField(choices=(
        (1, 'Network'), (2, 'Mobile'), (3, 'Domain PC'), (4, 'Hostname')), editable=False)
    computer = models.OneToOneField(tracking.Computer, null=True, editable=False)
    mobile = models.OneToOneField(tracking.Mobile, null=True, editable=False)
    username = models.CharField(max_length=128, null=True, editable=False)
    email = models.CharField(max_length=512, null=True, editable=False)
    ipv4 = models.TextField(default='', editable=False)
    ports = models.TextField(default='', editable=False)
    name = models.CharField(max_length=2048, unique=True, editable=False)
    serials = models.TextField(null=True, editable=False)
    local_info = models.TextField(null=True, editable=False)
    local_current = models.BooleanField(default=True, help_text='Does local state match central state?')
    os = models.ForeignKey(Software, on_delete=models.PROTECT, null=True, limit_choices_to={'os': True})

    def __str__(self):
        return '{}:{} ({})'.format(self.get_device_type_display(), self.name, self.cost_centre)

    class Meta:
        unique_together = ('computer', 'mobile')
        ordering = ('name', '-device_type')
        verbose_name_plural = 'hardware'


class Device(tracking.CommonFields):
    TYPE_CHOICES = (
        (0, "Computer"),
        (1, "Mobile"),
        (2, "PRTG"),
    )
    name = models.CharField(max_length=2048, unique=True)
    owner = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, null=True, related_name="devices_owned")
    guid = models.CharField(max_length=48, unique=True, help_text="AD GUID (ad:...) or PRTG object id (prtg:...)")
    device_type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=0)

    def __str__(self):
        return self.name


class UserGroup(models.Model):
    """A model to represent an arbitrary group of users for an IT System.
    E.g. 'All department staff', 'External govt agency staff', etc.
    """
    name = models.CharField(max_length=2048, unique=True)
    user_count = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.user_count)


class ITSystemHardware(models.Model):
    """A model to represent the relationship between an IT System and a
    Hardware entity.
    """
    ROLE_CHOICES = (
        (1, 'Application server'),
        (2, 'Database server'),
        (3, 'Network file storage'),
        (4, 'Reverse proxy'),
    )
    host = models.ForeignKey(Hardware, on_delete=models.PROTECT)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES)

    class Meta:
        verbose_name_plural = 'IT system hardware'
        unique_together = ('host', 'role')

    def __str__(self):
        return '{} ({})'.format(self.host.name, self.role)


class ITSystem(tracking.CommonFields):
    STATUS_CHOICES = (
        (0, "Production"),
        (1, "Development"),
        (2, "Production (Legacy)"),
        (3, "Decommissioned"),
        (4, "Unknown")
    )
    ACCESS_CHOICES = (
        (1, 'Public Internet'),
        (2, 'Authenticated Extranet'),
        (3, 'Corporate Network'),
        (4, 'Local System (Networked)'),
        (5, 'Local System (Standalone)')
    )
    AUTHENTICATION_CHOICES = (
        (1, 'Domain Credentials'),
        (2, 'Single Sign On'),
        (3, 'Externally Managed')
    )
    AVAILABILITY_CHOICES = (
        (1, '24 hours a day, 7 days a week, 365 days a year'),
        (2, 'Department core business hours'),
    )
    name = models.CharField(max_length=128, unique=True)
    system_id = models.CharField(max_length=16, unique=True)
    acronym = models.CharField(max_length=16, null=True, blank=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=4)
    status_display = models.CharField(max_length=128, null=True, editable=False)
    description = models.TextField(blank=True)
    devices = models.ManyToManyField(Device, blank=True)
    owner = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, null=True, related_name="systems_owned", help_text="Application owner")
    custodian = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, null=True, related_name="systems_custodianed", help_text="Appication custodian")
    data_custodian = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, related_name="systems_data_custodianed", null=True, blank=True)
    preferred_contact = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, related_name="systems_preferred_contact", null=True, blank=True)
    link = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to Application itself")
    documentation = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to Documentation")
    status_html = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to status/uptime info")
    authentication = models.PositiveSmallIntegerField(choices=AUTHENTICATION_CHOICES, default=1)
    authentication_display = models.CharField(max_length=128, null=True, editable=False)
    access = models.PositiveSmallIntegerField(choices=ACCESS_CHOICES, default=3)
    access_display = models.CharField(max_length=128, null=True, editable=False)
    request_access = models.TextField(blank=True)
    process = models.ForeignKey(Process, on_delete=models.PROTECT, null=True, blank=True)
    function = models.ForeignKey(Function, on_delete=models.PROTECT, null=True, blank=True)
    criticality = models.PositiveIntegerField(choices=CRITICALITY_CHOICES, null=True, blank=True)
    availability = models.PositiveIntegerField(choices=AVAILABILITY_CHOICES, null=True, blank=True, help_text='Expected availability for this IT System')
    schema_url = models.URLField(max_length=2000, null=True, blank=True)
    user_groups = models.ManyToManyField(UserGroup, blank=True, help_text='User group(s) that use this IT System')
    softwares = models.ManyToManyField(Software, blank=True, help_text='Software that is used to provide this IT System')
    hardwares = models.ManyToManyField(ITSystemHardware, blank=True, help_text='Hardware that is used to provide this IT System')
    itsystems = models.ManyToManyField('self', blank=True, help_text='Other IT Systems that help provide this IT System')

    def description_html(self):
        return mark_safe(self.description)

    def save(self, *args, **kwargs):
        if not self.system_id:
            self.system_id = "S{0:03d}".format(ITSystem.objects.order_by("-pk").first().pk+1)
        self.status_display = self.get_status_display()
        self.authentication_display = self.get_authentication_display()
        if not self.link:  # systems with no link default to device
            self.access = 4
        self.access_display = self.get_access_display()
        super(ITSystem, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "IT System"


class Backup(tracking.CommonFields):
    ROLE_CHOICES = (
        (0, "Generic Server"),
        (1, "Domain Controller"),
        (2, "Database Server"),
        (3, "Application Host"),
        (4, "Management Server"),
        (5, "Site Server"),
        (6, "File Server"),
        (7, "Print Server"),
        (8, "Block Storage Server"),
        (9, "Email Server"),
        (10, "Network Device"))
    STATUS_CHOICES = (
        (0, "Production"),
        (1, "Pre-Production"),
        (2, "Legacy"),
        (3, "Decommissioned")
    )
    SCHEDULE_CHOICES = (
        (0, "Manual"),
        (1, "Point in time, 7 day retention"),
        (2, "Daily, 7 day retention"),
        (3, "Daily, 30 day retention"),
        (4, "Weekly, 1 month retention")
    )
    system = models.OneToOneField(Hardware)
    operating_system = models.CharField(max_length=120)
    parent_host = models.ForeignKey(Hardware, on_delete=models.PROTECT, null=True, blank=True, related_name="host")
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=0)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=0)
    database_backup = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to Database backup/restore/logs info")
    database_schedule = models.PositiveSmallIntegerField(choices=SCHEDULE_CHOICES, default=0)
    filesystem_backup = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to Filesystem backup/restore/logs info")
    filesystem_schedule = models.PositiveSmallIntegerField(choices=SCHEDULE_CHOICES, default=0)
    appdata_backup = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to Application Data backup/restore/logs info")
    appdata_schedule = models.PositiveSmallIntegerField(choices=SCHEDULE_CHOICES, default=0)
    appconfig_backup = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to Config for App/Server")
    appconfig_schedule = models.PositiveSmallIntegerField(choices=SCHEDULE_CHOICES, default=0)
    os_backup = models.CharField(max_length=2048, null=True, blank=True, help_text="URL to Build Documentation")
    os_schedule = models.PositiveSmallIntegerField(choices=SCHEDULE_CHOICES, default=0)
    last_tested = models.DateField(null=True, blank=True, help_text="Last tested date")
    test_schedule = models.PositiveSmallIntegerField(default=12, help_text="Test Schedule in Months, 0 for never")
    comment = models.TextField(blank=True)

    def next_test_date(self):
        if self.test_schedule == 0:
            return "Doesn't require testing"
        if not self.last_tested:
            return "NEVER TESTED"
        else:
            return self.last_tested + relativedelta(months=self.test_schedule)

    def test_overdue(self):
        if self.test_schedule == 0:
            return False
        if not self.last_tested:
            return True
        return self.next_test_date() < timezone.now().date()

    def __str__(self):
        return "{} ({})".format(self.system.name.split(".")[0], self.get_status_display())

    class Meta:
        ordering = ("system__name",)


class Vendor(models.Model):
    name = models.CharField(max_length=256, unique=True)
    details = models.TextField(blank=True)
    extra_data = JSONField(default=dict(), null=True, blank=True)

    def __str__(self):
        return self.name


class SoftwareLicense(tracking.CommonFields):
    """
    Represents a software licensing arrangement.
    """
    name = models.CharField(max_length=256, unique=True)
    url = models.URLField(max_length=2000, null=True, blank=True)
    support = models.TextField(blank=True, help_text='Support timeframe or scope')
    support_url = models.URLField(max_length=2000, null=True, blank=True)
    oss = models.NullBooleanField(default=None, help_text='Open-source/free software license?')
    primary_user = models.ForeignKey(tracking.DepartmentUser, on_delete=models.PROTECT, null=True, blank=True)
    devices = models.ManyToManyField(Device, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, null=True, blank=True)
    used_licenses = models.PositiveSmallIntegerField(default=0, editable=False)
    available_licenses = models.PositiveSmallIntegerField(default=0)
    license_details = models.TextField(blank=True, help_text="Direct license keys or details")

    def __str__(self):
        return self.name


class BusinessService(models.Model):
    """Represents the Department's core business services.
    """
    number = models.PositiveIntegerField(unique=True, help_text='Service number')
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return 'Service {}: {}'.format(self.number, self.name)


class BusinessFunction(models.Model):
    """Represents a function of the Department, undertaken to meet the
    Department's core services. Each function must be linked to 1+
    BusinessService object.
    """
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField(null=True, blank=True)
    services = models.ManyToManyField(BusinessService)

    def __str__(self):
        return self.name


class BusinessProcess(models.Model):
    """Represents a business process that the Department undertakes in order
    to fulfil one of the Department's functions.
    """
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField(null=True, blank=True)
    functions = models.ManyToManyField(BusinessFunction)

    class Meta:
        verbose_name_plural = 'business processes'

    def __str__(self):
        return self.name


class ProcessITSystemRelationship(models.Model):
    """A model to represent the relationship between a BusinessProcess and an
    ITSystem object.
    """
    process = models.ForeignKey(BusinessProcess, on_delete=models.PROTECT)
    itsystem = models.ForeignKey(ITSystem, on_delete=models.PROTECT)
    criticality = models.PositiveIntegerField(choices=CRITICALITY_CHOICES)

    class Meta:
        unique_together = ('process', 'itsystem')
