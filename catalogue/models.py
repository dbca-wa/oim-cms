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

from django.db import models,connection
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, post_delete,pre_delete
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import md5
import base64
import os
import re
import json

slug_re = re.compile(r'^[a-z0-9_]+$')
validate_slug = RegexValidator(slug_re, "Slug can only contain lowercase letters, numbers and underscores", "invalid")

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
    service_type_version = models.CharField(max_length=10, blank=True)

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
    title = models.CharField(max_length=255, null=True,blank=True,
                             help_text='Maps to pycsw:Title')
    typename = models.CharField(
        max_length=100, default="", db_index=True, blank=True,
        help_text="Maps to pycsw:Typename", editable=False
    )
    schema = models.CharField(
        max_length=100, default="",
        help_text="Maps to pycsw:Schema", db_index=True, blank=True, editable=False
    )
    insert_date = models.DateTimeField(
        auto_now_add=True, help_text='Maps to pycsw:InsertDate')
    xml = models.TextField(
        default='',
        editable=False,
        help_text=' Maps to pycsw:XML'
    )
    any_text = models.TextField(help_text='Maps to pycsw:AnyText',null=True, blank=True)
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
        max_length=30, null=True, blank=True,editable=False,
        help_text='Maps to pycsw:ServiceTypeVersion'
    )
    links = models.TextField(null=True, blank=True,editable=False,
                             help_text='Maps to pycsw:Links')
    crs = models.CharField(max_length=255, null=True, blank=True,help_text='Maps to pycsw:CRS')
    # Custom fields
    auto_update = models.BooleanField(default=True)
    active = models.BooleanField(default=True, editable=False)
    
    def __unicode__(self):
        return self.identifier

    def default_style(self,format):
        try:
            return self.styles.get(format=format,default=True)
        except Style.DoesNotExist:
            return None

    def get_resources(self,_type):
        if self.links:
            resources = re.split(",\s*(?=[^}]*(?:\{|$))",self.links)
        else:
            resources = []
        if _type =='style':
            style_resources = []
            for r in resources:
                r = json.loads(r)
                if r['protocol'] == 'FILE:GEO':
                    style_resources.append(r)
            resources = style_resources
        elif _type == 'ows':
            ows_resources = []
            for r in resources:
                r = json.loads(r)
                if 'OGC' in r['protocol']:
                    ows_resources.append(r)
            resources = ows_resources
        return resources

    @staticmethod
    def generate_ows_link(service_type,service_version,record):
        if service_type == 'WFS':
            link = '{0}?SERVICE={1}&VERSION={2}&REQUEST=GetMap&BBOX={3}&CRS={4}&LAYERS={4}'.format(
            enpoint,service_type.upper(),service_version,record.bounding_box,record.crs,record.identifier)
        else:
            link = '{0}?SERVICE={1}&VERSION={2}&REQUEST=GetMap&BBOX={3}&CRS={4}&WIDTH=500&HEIGHT=400&LAYERS={5}&FORMAT=image/png'.format(
            enpoint,service_type.upper(),service_version,record.bounding_box,record.crs,record.identifier)
        return '{{"protocol": "OGC:{0}","linkage":"{1}"}}'.format(service_type.upper(),link)

    @staticmethod
    def generate_style_link(style):
        link =  '{{"protocol": "application:{0}","name":"{1}","format":"{2}","linkage":"{3}/media/{4}"}}'.format(style.format.lower(),style.name,style.format,settings.BASE_URL,style.content)
        return link

    @staticmethod
    def update_style_links(resources,record):
        pos = 1
        links = ''
        for r in resources:
            if pos == 1:
                links += '{0}'.format(json.dumps(r))
            else:
                links += ',{0}'.format(json.dumps(r))
            pos += 1
        record.links = links
        record.save()

    @property
    def style_resources(self):
        return self.get_resources('style')

    @property
    def ows_resources(self):
        return self.get_resources('ows')
    
    @property
    def sld(self):
        """
        The default sld style file
        if not exist, return None
        """
        return self.default_style("SLD")
    
    @property
    def lyr(self):
        """
        The default lyr style file
        if not exist, return None
        """
        return self.default_style("LYR")
    
    @property
    def qml(self):
        """
        The default qml style file
        if not exist, return None
        """
        return self.default_style("QML")
    
    def clean(self):
        #set auto update to false if some columns are changed
        if self.pk and self.auto_update:
            origin = Record.objects.get(pk = self.pk)
            if any([(getattr(origin,k) or "") != (getattr(self,k) or "") for k in ["title","abstract"]]):
                self.auto_update = False
                    
    """
    Used to check the default style
    for a particular format. If it does
    not exist it sets the first style as
    the default
    Return the configured default style; otherwise return None
    """
    def setup_default_styles(self,format):
        default_style = self.default_style(format)
        if default_style:
            return default_style
        else:
            style = None
            try:
                #no default style is configured, try to get the builtin one as the default style
                style = self.styles.get(format=format,name=Style.BUILTIN)
            except:
                #no builtin style  try to get the first added one as the default style
                style = self.styles.filter(format=format).order_by("name").first()
            if style:
                style.default = True
                style.save(update_fields=["default"])
                return style
            else:
                return None

    
    def delete(self,using=None):
        if self.active:
            raise ValidationError("Can not delete the active record ({}).".format(self.identifier))
        else:
            super(Record,self).delete(using)

    class Meta:
        ordering = ['identifier']

class Style(models.Model):
    BUILTIN = "builtin"
    FORMAT_CHOICES = (
        ('SLD','SLD'),
        ('QML','QML'),
        ('LYR','LAYER')
    )
    record = models.ForeignKey(Record, related_name='styles')
    name = models.CharField(max_length=255)
    format = models.CharField(max_length=3, choices=FORMAT_CHOICES)
    default = models.BooleanField(default=False)
    content = models.FileField(upload_to='catalogue/styles')
    checksum = models.CharField(blank=True,max_length=255, editable=False)

    @property
    def identifier(self):
        return "{}:{}".format(self.record.identifier,self.name)

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.pk and self.name == Style.BUILTIN:
            raise ValidationError("Can't add a builtin style.")

        """
        simply reset the default style to the current style if the current style is configured as default style
        if getattr(self,"record",None) and self.default:
            try:
                duplicate = Style.objects.exclude(pk=self.pk).get(record=self.record,format=self.format,default=True)
                if duplicate and self.default:
                    raise ValidationError('There can only be one default format style for each record')
            except Style.DoesNotExist:
                pass
        """

    @property
    def can_delete(self):
        if not self.pk or self.name == Style.BUILTIN:
            return False
        return True
            
    def delete(self,using=None):
        if self.name == Style.BUILTIN:
            raise ValidationError("Can not delete builtin style.")
        else:
            super(Style,self).delete(using)

    def save(self, *args, **kwargs):
        update_fields=None
        clean_name = self.name.split('.')
        self.content.name = 'catalogue/styles/{}_{}.{}'.format(self.record.identifier.replace(':','_'),clean_name[0],self.format.lower())
        if self.pk is not None:
            update_fields=kwargs.get("update_fields",["default","content","checksum"])
            if "content" in update_fields:
                if "checksum" not in update_fields: update_fields.append("checksum")
                orig = Style.objects.get(pk=self.pk)
                if orig.content:
                    if orig.checksum != self._calculate_checksum(self.content):
                        if os.path.isfile(orig.content.path):
                            os.remove(orig.content.path)

                        if os.path.isfile(self.content.path):
                            #the style file exists in the file system, remove it
                            os.remove(self.content.path)

                        if self.record.auto_update:
                            #auto update is enabled
                            if getattr(self,"access_channel","django-admin") == "django-admin":
                                #changed from django admin portal, disable auto_update
                                self.record.auto_update = False
                                self.record.save(update_fields=["auto_update"])
                    else:
                        #content is not changed, no need to update content and checksum
                        update_fields = [field for field in update_fields if field not in ["content","checksum"]]
                        if not update_fields:
                            #nothing is needed to update.
                            return
                else:
                    if os.path.isfile(orig.content.path):
                        os.remove(orig.content.path)
                    if os.path.isfile(self.content.path):
                        #the style file exists in the file system, remove it
                        os.remove(self.content.path)

        if update_fields:
            kwargs["update_fields"] = update_fields
        super(Style, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return self.name
    
    def _calculate_checksum(self, content):
        checksum = md5.new()
        checksum.update(content.read())
        return base64.b64encode(checksum.digest())

@receiver(pre_save,sender=Style)
def update_style_links(sender, instance, **kwargs):
    link = Record.generate_style_link(instance)
    json_link = json.loads(link)
    present = False
    style_resources = instance.record.style_resources
    ows_resources = instance.record.ows_resources
    if not instance.record.links:
        instance.record.links = ''
    for r in style_resources:
        if r['name'] == json_link['name'] and r['format'] == json_link['format']:
            present = True
    if not present:
        style_resources.append(json_link)
        resources = ows_resources + style_resources
        Record.update_style_links(resources,instance.record)

@receiver(post_delete,sender=Style)
def remove_style_links(sender, instance, **kwargs):
    style_resources = instance.record.style_resources
    ows_resources = instance.record.ows_resources
    for r in style_resources:
        if r['name'] == instance.name and r['format'] == instance.format:
            style_resources.remove(r)
            resources = ows_resources + style_resources
            Record.update_style_links(resources,instance.record)

@receiver(pre_save, sender=Style)
def set_default_style (sender, instance, **kwargs):
    update_fields=kwargs.get("update_fields",None)
    if not instance.pk or not update_fields or "default" in update_fields:
        if instance.default:
            #The style will be set as the default style
            cur_default_style = instance.record.default_style(instance.format)
            if cur_default_style and cur_default_style.pk != instance.pk:
                #The current default style is not the saving style, reset the current default style's default to false
                cur_default_style.default=False
                cur_default_style.save(update_fields=["default"])
        else:
            #The saving style is not the default style, try to set a default style if it does not exist
            default_style = instance.record.setup_default_styles(instance.format)
            if not default_style or default_style.pk == instance.pk:
                #no default style is configured,set the current one as default style
                instance.default = True

@receiver(pre_save, sender=Style)
def set_checksum (sender, instance, **kwargs):
    update_fields=kwargs.get("update_fields",None)
    if not update_fields or "checksum" in update_fields:
        checksum = md5.new()
        checksum.update(instance.content.read())
        instance.checksum = base64.b64encode(checksum.digest())

@receiver(post_delete, sender=Style)
def auto_remove_style_from_disk_on_delete(sender, instance, **kwargs):
    """ Deletes the style file from disk when the
        object is deleted
    """
    if instance.default:
        #deleted style is the default style, reset the default style
            instance.record.setup_default_styles(instance.format)

    if instance.content:
        if os.path.isfile(instance.content.path):
            os.remove(instance.content.path)


class Application(models.Model):
    """
    Represent a application which can access wms,wfs,wcs service from geoserver
    """
    name = models.CharField(max_length=255, validators=[validate_slug],unique=True,blank=False)
    description = models.TextField(blank=True)
    last_modify_time = models.DateTimeField(auto_now=True,null=False)
    create_time = models.DateTimeField(auto_now_add=True,null=False)

    @staticmethod
    def get_view_name(app):
        return "catalogue_record_{}".format(app)


    @property
    def records_view(self):
        return Application.get_view_name(self.name)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class ApplicationEventListener(object):
    @staticmethod
    @receiver(pre_delete, sender=Application)
    def _pre_delete(sender, instance, **args):
        #remove the view for this application
        try:
            cursor = connection.cursor()
            cursor.execute("DROP VIEW {} CASCADE".format(instance.records_view))
        except:
            #drop failed, maybe the view does not exist, ignore the exception
            connection._rollback()


    @staticmethod
    @receiver(pre_save, sender=Application)
    def _pre_save(sender, instance, **args):
        #create a view for this application
        try:
            cursor = connection.cursor()
            cursor.execute("CREATE OR REPLACE VIEW {} AS SELECT r.* FROM catalogue_application a join catalogue_applicationlayer l on a.id = l.application_id join catalogue_record r on l.layer_id = r.id WHERE a.name = '{}' and r.active order by l.order,r.identifier".format(instance.records_view,instance.name))
        except Exception as e:
            #create view failed
            connection._rollback()
            raise ValidationError(e)

class ApplicationLayer(models.Model):
    """
    The relationship between application and layer
    """
    application = models.ForeignKey(Application,blank=False,null=False)
    layer = models.ForeignKey(Record,null=False,blank=False,limit_choices_to={"active":True})
    order = models.PositiveIntegerField(blank=False,null=False)

    def __str__(self):
        return "{}:{}".format(self.application.name,self.layer.identifier)

    class Meta:
        unique_together = (('application','layer'))
        ordering = ['application','order','layer']


