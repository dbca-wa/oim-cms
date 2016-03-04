from __future__ import unicode_literals, absolute_import
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.html import format_html
from mptt.models import MPTTModel, TreeForeignKey
from json2html import json2html
import os


class CommonFields(models.Model):
    """
    Fields to be added to all tracking model classes
    """
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    org_unit = models.ForeignKey("registers.OrgUnit", on_delete=models.PROTECT, null=True, blank=True)
    cost_centre = models.ForeignKey("registers.CostCentre", on_delete=models.PROTECT, null=True)
    extra_data = JSONField(null=True, blank=True)

    def extra_data_pretty(self):
        if not self.extra_data:
            return self.extra_data
        try:
            return format_html(json2html.convert(json=self.extra_data))
        except Exception as e:
            return repr(e)

    def save(self, *args, **kwargs):
        if self.cost_centre and not self.org_unit:
            self.org_unit = self.cost_centre.org_position
        elif self.cost_centre and self.org_unit not in self.cost_centre.org_position.get_descendants(include_self=True):
            self.org_unit = self.cost_centre.org_position
        super(CommonFields, self).save(*args, **kwargs)

    class Meta:
        abstract = True


# python 2 can't serialize unbound functions, so here's some dumb glue
def get_photo_path(instance, filename='photo.jpg'):
    return os.path.join("user_photo", '{0}.{1}'.format(instance.id, os.path.splitext(filename)))

def get_photo_ad_path(instance, filename='photo.jpg'):
    return os.path.join("user_photo_ad", '{0}.{1}'.format(instance.id, os.path.splitext(filename)))


class DepartmentUser(MPTTModel):
    """
    Represents a Department user.
    This model maps to an object managed by Active Directory.
    """
    ACTIVE_FILTER = {"active": True, "email__isnull": False, "cost_centre__isnull": False, "contractor": False}
    # These fields are populated from Active Directory.
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    cost_centre = models.ForeignKey("registers.CostCentre", on_delete=models.PROTECT, null=True)
    org_unit = models.ForeignKey("registers.OrgUnit", on_delete=models.PROTECT, null=True, blank=True)
    extra_data = JSONField(null=True, blank=True)
    ad_guid = models.CharField(max_length=48, unique=True, editable=False)
    ad_dn = models.CharField(max_length=512, unique=True, editable=False)
    ad_data = JSONField(null=True, editable=False)
    org_data = JSONField(null=True, editable=False)
    employee_id = models.CharField(max_length=128, null=True, unique=True, blank=True, help_text="HR Employee ID, use 'n/a' if a contractor")
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=128, editable=False, unique=True)
    given_name = models.CharField(max_length=128, null=True)
    surname = models.CharField(max_length=128, null=True)
    title = models.CharField(max_length=128, null=True, help_text='Staff position')
    email = models.EmailField(unique=True, editable=False)
    parent = TreeForeignKey('self', on_delete=models.PROTECT, null=True, related_name='children', editable=True, blank=True)
    expiry_date = models.DateTimeField(null=True, editable=False)
    date_ad_updated = models.DateTimeField(null=True, editable=False)
    telephone = models.CharField(max_length=128, null=True, blank=True)
    mobile_phone = models.CharField(max_length=128, null=True, blank=True)
    home_phone = models.CharField(max_length=128, null=True, blank=True)
    other_phone = models.CharField(max_length=128, null=True, blank=True)
    active = models.BooleanField(default=True, editable=False)
    ad_deleted = models.BooleanField(default=False, editable=False)
    in_sync = models.BooleanField(default=False, editable=False)
    vip = models.BooleanField(default=False, help_text="An individual who carries out a critical role for the department")
    executive = models.BooleanField(default=False, help_text="An individual who is an executive")
    contractor = models.BooleanField(default=False, help_text="An individual who is an external contractor")
    photo = models.ImageField(blank=True, upload_to=get_photo_path)
    photo_ad = models.ImageField(blank=True, editable=False, upload_to=get_photo_ad_path)
    sso_roles = models.TextField(null=True, editable=False, help_text="Groups/roles separated by semicolon")
    notes = models.TextField(null=True, blank=True, help_text="Officer secondary roles, etc.")
    working_hours = models.TextField(default="9:00-17:00, Mon-Fri", null=True, blank=True, help_text="Officer normal work/contact hours")

    def save(self, *args, **kwargs):
        if self.employee_id and self.employee_id.lower() == "n/a":
            self.employee_id = None
        if self.employee_id:
            self.employee_id = "{0:06d}".format(int(self.employee_id))
        self.in_sync = getattr(self, "ad_updated", False)
        if self.cost_centre and not self.org_unit:
            self.org_unit = self.cost_centre.org_position
        if self.cost_centre:
            self.org_data = self.org_data or {}
            self.org_data["units"] = list(self.org_unit.get_ancestors(include_self=True).values("name", "acronym", "unit_type", "costcentre__code", "costcentre__name", "location__name"))
            self.org_data["unit"] = self.org_data["units"][-1]
            if self.org_unit.location:
                self.org_data["location"] = self.org_unit.location.as_dict()
            if self.org_unit.secondary_location:
                self.org_data["secondary_location"] = self.org_unit.secondary_location.as_dict()
            for unit in self.org_data["units"]:
                unit["unit_type"] = self.org_unit.TYPE_CHOICES_DICT[unit["unit_type"]]
            self.org_data["cost_centre"] = {
                "name": self.org_unit.name,
                "code": self.cost_centre.code,
                "manager": str(self.cost_centre.manager),
                "business_manager": str(self.cost_centre.business_manager),
                "admin": str(self.cost_centre.admin),
                "tech_contact": str(self.cost_centre.tech_contact),
            }

        self.update_photo_ad()
        super(DepartmentUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.email

    def update_photo_ad(self):
        # update self.photo_ad to contain a thumbnail less than 240x240 and 10kb
        if not self.photo:
            if self.photo_ad:
                self.photo_ad.delete()
            return

        from PIL import Image
        from cStringIO import StringIO
        from django.core.files.base import ContentFile

        if hasattr(self.photo.file, 'content_type'):
            PHOTO_TYPE = self.photo.file.content_type

            if PHOTO_TYPE == 'image/jpeg':
                PIL_TYPE = 'jpeg'
            elif PHOTO_TYPE == 'image/png':
                PIL_TYPE = 'png'
            else:
                return
        else:
            PIL_TYPE = 'jpeg'
        # good defaults to get ~10kb JPEG images
        PHOTO_AD_SIZE = (240, 240)
        PIL_QUALITY = 75
        # remote file size limit
        PHOTO_AD_FILESIZE = 10000

        image = Image.open(StringIO(self.photo.read()))
        image.thumbnail(PHOTO_AD_SIZE, Image.LANCZOS)

        # in case we miss 10kb, drop the quality and recompress
        for i in range(12):
            temp_buffer = StringIO()
            image.save(temp_buffer, PIL_TYPE, quality=PIL_QUALITY, optimize=True)
            length = temp_buffer.tell()
            if length <= PHOTO_AD_FILESIZE:
                break
            if PIL_TYPE == 'png':
                PIL_TYPE = 'jpeg'
            else:
                PIL_QUALITY -= 5

        temp_buffer.seek(0)
        self.photo_ad.save(os.path.basename(self.photo.name), ContentFile(temp_buffer.read()), save=False)

    def org_data_pretty(self):
        if not self.org_data:
            return self.org_data
        return format_html(json2html.convert(json=self.org_data))

    def ad_data_pretty(self):
        if not self.ad_data:
            return self.ad_data
        return format_html(json2html.convert(json=self.ad_data))

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        ordering = ('name',)


class Computer(CommonFields):
    """
    Represents a non-mobile computing device.
    This model maps to an object managed by Active Directory.
    """
    sam_account_name = models.CharField(max_length=32, unique=True, null=True)
    hostname = models.CharField(max_length=2048)
    domain_bound = models.BooleanField(default=False)
    ad_guid = models.CharField(max_length=48, null=True, unique=True)
    ad_dn = models.CharField(max_length=512, null=True, unique=True)
    pdq_id = models.IntegerField(null=True, blank=True, unique=True)
    sophos_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    asset_id = models.CharField(max_length=64, null=True, blank=True, help_text='OIM Asset ID')
    finance_asset_id = models.CharField(
        max_length=64, null=True, blank=True, help_text='Finance asset ID')
    manufacturer = models.CharField(max_length=128)
    model = models.CharField(max_length=128)
    chassis = models.CharField(max_length=128)
    serial_number = models.CharField(max_length=128)
    os_name = models.CharField(max_length=128, blank=True)
    os_version = models.CharField(max_length=128)
    os_service_pack = models.CharField(max_length=128)
    os_arch = models.CharField(max_length=128)
    cpu = models.CharField(max_length=128)
    cpu_count = models.PositiveSmallIntegerField(default=0)
    cpu_cores = models.PositiveSmallIntegerField(default=0)
    memory = models.BigIntegerField(default=0)
    probable_owner = models.ForeignKey(DepartmentUser, on_delete=models.PROTECT, blank=True, null=True, related_name='computers_probably_owned',
                                       help_text='Automatically-generated "most probable" device owner.')
    managed_by = models.ForeignKey(DepartmentUser, on_delete=models.PROTECT, blank=True, null=True, related_name='computers_managed',
                                   help_text='"Official" device owner/manager (set in AD).')
    date_pdq_updated = models.DateTimeField(null=True, blank=True)
    date_nmap_updated = models.DateTimeField(null=True, blank=True)
    date_sophos_updated = models.DateTimeField(null=True, blank=True)
    date_ad_updated = models.DateTimeField(null=True, blank=True)
    date_dhcp_updated = models.DateTimeField(null=True, blank=True)
    # Notes field to store validation results from synchronising
    # user-uploaded local property register spreadsheets.
    validation_notes = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.sam_account_name


class Mobile(CommonFields):
    """
    Represents a mobile computing device.
    """
    ad_guid = models.CharField(max_length=48, null=True, unique=True)
    ad_dn = models.CharField(max_length=512, null=True, unique=True)
    registered_to = models.ForeignKey(DepartmentUser, on_delete=models.PROTECT, blank=True, null=True)
    asset_id = models.CharField(max_length=64, null=True, help_text='OIM Asset ID')
    finance_asset_id = models.CharField(
        max_length=64, null=True, help_text='Finance asset ID')
    model = models.CharField(max_length=128, null=True)
    os_name = models.CharField(max_length=128, null=True)
    # Identity is a GUID, from Exchange.
    identity = models.CharField(max_length=512, null=True, unique=True)
    serial_number = models.CharField(max_length=128, null=True)
    imei = models.CharField(max_length=64, null=True)
    last_sync = models.DateTimeField(null=True)

    def __unicode__(self):
        return unicode(self.identity)


class EC2Instance(CommonFields):
    name = models.CharField("Instance Name", max_length=200)
    ec2id = models.CharField("EC2 Instance ID", max_length=200, unique=True)
    launch_time = models.DateTimeField(editable=False, null=True, blank=True)
    next_state = models.BooleanField(default=True, help_text="Checked is on, unchecked is off")
    running = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'EC2 instance'
