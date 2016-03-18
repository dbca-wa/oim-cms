"""
Testing can be done on the command line using httpie:

.. code:: bash

   http --pretty=all --verbose http://localhost:8000/ \
       service==CSW \
       version==2.0.2 \
       request==GetRecordById \
       Id==c1fdc10a-9170-11e4-ba66-0019995d2a58 \
       ElementSetName==full \
       Outputschema==http://www.isotc211.org/2005/gmd \
       | less -R

Or with the browser and GET requests:

http://localhost:8000/csw/server/?
    SERVICE=CSW&version=2.0.2&
    REQUEST=GetRecords&
    resultType=results&
    constraintLanguage=CQL_TEXT&
    constraint_language_version=1.1.0&
    constraint=TempExtent_begin%20%3E=%20%272014-10-12T00:00:00Z%27&
    elementSetName=full&
    outputSchema=http://www.isotc211.org/2005/gmd&
    typenames=gmd:MD_Metadata

"""

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.conf import settings
import md5
import base64

class PycswConfig(models.Model):
    language = models.CharField(max_length=10, default="en-US")
    max_records = models.IntegerField(default=10)
    #log_level  # can use django's config
    #log_file  # can use django's config
    #ogc_schemas_base
    #federated_catalogues
    #pretty_print
    #gzip_compress_level
    #domain_query_type
    #domain_counts
    #spatial_ranking
    transactions = models.BooleanField(default=False,
                                       help_text="Enable transactions")
    allowed_ips = models.CharField(
        max_length=255, blank=True, default="127.0.0.1",
        help_text="IP addresses that are allowed to make transaction requests"
    )
    harvest_page_size = models.IntegerField(default=10)
    title = models.CharField(max_length=50)
    abstract = models.TextField()
    keywords = models.CharField(max_length=255)
    keywords_type = models.CharField(max_length=255)
    fees = models.CharField(max_length=100)
    access_constraints = models.CharField(max_length=255)
    point_of_contact = models.ForeignKey("Collaborator")
    repository_filter = models.CharField(max_length=255, blank=True)
    inspire_enabled = models.BooleanField(default=False)
    inspire_languages = models.CharField(max_length=255, blank=True)
    inspire_default_language = models.CharField(max_length=30, blank=True)
    inspire_date = models.DateTimeField(null=True, blank=True)
    gemet_keywords = models.CharField(max_length=255, blank=True)
    conformity_service = models.CharField(max_length=255, blank=True)
    temporal_extent_start = models.DateTimeField(null=True, blank=True)
    temporal_extent_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "PyCSW Configuration"
        verbose_name_plural = "PyCSW Configuration"


class Organization(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=30)
    url = models.URLField()
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state_or_province = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return self.short_name


class Collaborator(models.Model):
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    email = models.EmailField()
    organization = models.ForeignKey(Organization,
                                     related_name="collaborators")
    url = models.URLField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)
    hours_of_service = models.CharField(max_length=50, blank=True)
    contact_instructions = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return "{}({})".format(self.name, self.organization.short_name)

class Record(models.Model):
    identifier = models.CharField(
        max_length=255, db_index=True, help_text="Maps to pycsw:Identifier")
    title = models.CharField(max_length=255, null=True,
                             help_text='Maps to pycsw:Title')
    typename = models.CharField(
        max_length=100, default="gmd:MD_Metadata", db_index=True,
        help_text="Maps to pycsw:Typename"
    )
    schema = models.CharField(
        max_length=100, default="http://www.isotc211.org/2005/gmd",
        help_text="Maps to pycsw:Schema", db_index=True,
    )
    insert_date = models.DateTimeField(
        auto_now_add=True, help_text='Maps to pycsw:InsertDate')
    xml = models.TextField(
        default='<gmd:MD_Metadata '
                'xmlns:gmd="http://www.isotc211.org/2005/gmd"/>',
        help_text=' Maps to pycsw:XML'
    )
    any_text = models.TextField(help_text='Maps to pycsw:AnyText')
    modified = models.DateTimeField(
        null=True, blank=True,
        help_text='Maps to pycsw:Modified'
    )
    bounding_box = models.TextField(null=True, blank=True,
                                    help_text='Maps to pycsw:BoundingBox.It\'s a WKT geometry')
    abstract = models.TextField(blank=True, null=True,
                                help_text='Maps to pycsw:Abstract')
    keywords = models.CharField(max_length=255, blank=True, null=True,
                                help_text='Maps to pycsw:Keywords')
    publication_date = models.DateTimeField(
        null=True, blank=True,
        help_text='Maps to pycsw:PublicationDate'
    )
    service_type = models.CharField(max_length=30, null=True, blank=True,
                                    help_text='Maps to pycsw:ServiceType')
    service_type_version = models.CharField(
        max_length=30, null=True, blank=True,
        help_text='Maps to pycsw:ServiceTypeVersion'
    )
    links = models.TextField(null=True, blank=True,
                             help_text='Maps to pycsw:Links')
    crs = models.CharField(max_length=255, null=True, blank=True,help_text='Maps to pycsw:CRS')
    # Custom fields
    auto_update = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    # Styles
    sld = models.CharField(max_length=255,blank=True, null=True,)
    qml = models.CharField(max_length=255,blank=True, null=True,)
    lyr = models.CharField(max_length=255,blank=True, null=True,)
    
    def __unicode__(self):
        return self.identifier
    
class Style(models.Model):
    FORMAT_CHOICES = (
        ('SLD','SLD'),
        ('QML','QML'),
        ('LYR','LAYER')
    )
    record = models.ForeignKey(Record, related_name='styles',null=True)
    name = models.CharField(max_length=255)
    format = models.CharField(max_length=3, choices=FORMAT_CHOICES)
    default = models.BooleanField(default=False)
    content = models.FileField(upload_to='{0}/catalogue/styles'.format(settings.MEDIA_ROOT),blank=True, default='')
    checksum = models.CharField(blank=True,max_length=255, editable=False)
    def clean(self):
        from django.core.exceptions import ValidationError
        try:
            duplicate = Style.objects.exclude(pk=self.pk).get(record=self.record,format=self.format,default=True)
            if duplicate and self.default:
                raise ValidationError('There can only be one default format style for each record')
        except Style.DoesNotExist:
            pass
    def __unicode__(self):
        return self.name
    
@receiver(post_save, sender=Style)    
def setup_default_styles(sender, instance, **kwargs):
    record = Record.objects.get(id=instance.record_id)
    if instance.default:
        if instance.format == 'SLD':
            record.sld = instance.name
        elif instance.format == 'QML':
            record.qml = instance.name
        elif instance.format == 'LYR':
            record.lyr = instance.name
    record.save()

@receiver(pre_save, sender=Style)
def set_checksum(sender, instance, **kwargs):
    checksum = md5.new()
    checksum.update(instance.content.read())
    instance.checksum = base64.b64encode(checksum.digest())
    
    
