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
import math

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

    bbox_re = re.compile('POLYGON\s*\(\(([\+\-0-9\.]+)\s+([\+\-0-9\.]+)\s*\,\s*[\+\-0-9\.]+\s+[\+\-0-9\.]+\s*\,\s*([\+\-0-9\.]+)\s+([\+\-0-9\.]+)\s*\,\s*[\+\-0-9\.]+\s+[\+\-0-9\.]+\s*\,\s*[\+\-0-9\.]+\s+[\+\-0-9\.]+\s*\)\)')

    @property 
    def bbox(self):
        if self.bounding_box:
            try:
                return [float(v) for v in self.bbox_re.match(self.bounding_box).groups()]
            except:
                return None
        else:
            return None
    
    def __unicode__(self):
        return self.identifier

    def default_style(self,format):
        try:
            return self.styles.get(format=format,default=True)
        except Style.DoesNotExist:
            return None
    
    @property
    def ows_resource(self ):
        links = self.ows_links
        resources = []
        for link in links:
            r = re.split("\t",link)
            sample_link = r[3]
            r = json.loads(r[2].replace("'","\""))
            if 'WMS' in r['protocol']:
                _type = 'WMS'
            elif 'WFS' in r['protocol']:
                _type = 'WFS'
            resource = {
                'type': _type,
                'version': r['version'],
                'endpoint': r['linkage'],
                'link': sample_link
            }
            resources.append(resource)
        return resources

    @property
    def style_links(self):
        return self.get_resource_links('style')

    @property
    def ows_links(self):
        return self.get_resource_links('ows')
    
    def get_resource_links(self,_type):
        if self.links:
            links = self.links.split('^')
        else:
            links = []
        if _type =='style':
            style_links = []
            for link in links:
                r = re.split("\t",link)
                r_json = json.loads(r[2].replace("'","\""))
                if 'application' in r_json['protocol']:
                    style_links.append(link)
            links = style_links
        elif _type == 'ows':
            ows_links = []
            for link in links:
                r = re.split("\t",link)
                r_json = json.loads(r[2].replace("'","\""))
                if 'OGC' in r_json['protocol']:
                    ows_links.append(link)
            links = ows_links
        return links

    def _calculate_from_bbox(self,side):
        bbox = []
        if self.bounding_box:
            try:
                bbox = json.loads(self.bounding_box)
                if not bbox or not isinstance(bbox,list) or len(bbox) != 4:
                    if side == 'width':
                        return 400
                    elif side == 'height':
                        return 500
            except:
                if side == 'width':
                    return 400
                elif side == 'height':
                    return 500

            if side == 'width':
                return int(bbox[2]) - int(bbox[0])
            elif side == 'height':
                return int(bbox[3]) - int(bbox[1])

    def generate_ows_link(self,endpoint,service_type,service_version):
        if service_version in ("1.1.0","1.1"):
            service_version = "1.1.0"
        elif service_version in ("2.0.0","2","2.0"):
            service_version = "2.0.0"
        elif service_version in ("1","1.0","1.0.0"):
            service_version = "1.0.0"

        bbox = self.bbox or []
        if bbox:
            if service_type == "WFS":
                #to limit the returned features, shrink the original bbox to 10 percent
                percent = 0.1
                shrinked_min = lambda min,max :(max - min) / 2 - (max - min) * percent / 2
                shrinked_max = lambda min,max :(max - min) / 2 + (max - min) * percent / 2
                shrinked_bbox = [shrinked_min(bbox[0],bbox[2]),shrinked_min(bbox[1],bbox[3]),shrinked_max(bbox[0],bbox[2]),shrinked_max(bbox[1],bbox[3])]
        else:
            shrinked_bbox = None

        bbox2str = lambda bbox,service,version: ','.join(str(c) for c in bbox) if service != "WFS" or version == "1.0.0" else ",".join([str(c) for c in [bbox[1],bbox[0],bbox[3],bbox[2]]])

        if service_type == "WFS":
            kvp = {
                "SERVICE":"WFS",
                "REQUEST":"GetFeature",
                "VERSION":service_version,
                "SRSNAME":self.crs,
                "TYPENAMES":self.identifier,
            }
            is_geoserver = endpoint.find("geoserver") >= 0

            if service_version == "1.1.0":
                if is_geoserver:
                    kvp["maxFeatures"] = 20
                elif shrinked_bbox:
                    kvp["BBOX"] = bbox2str(shrinked_bbox,service_type,service_version)
            elif service_version == "2.0.0":
                if is_geoserver:
                    kvp["count"] = 20
                elif shrinked_bbox:
                    kvp["BBOX"] = bbox2str(shrinked_bbox,service_type,service_version)
            else:
                kvp["BBOX"] = bbox2str(shrinked_bbox,service_type,service_version)
        elif service_type == "WMS":
            kvp = {
                "SERVICE":"WMS",
                "REQUEST":"GetMap",
                "VERSION":service_version,
                "SRSNAME":self.crs,
                "LAYERS":self.identifier,
                ("SRS","CRS"):self.crs,
                "WIDTH":self.width,
                "HEIGHT":self.height,
                "FORMAT":"image/png"
            }
            if bbox:
                kvp["BBOX"] = bbox2str(bbox,service_type,service_version)
        elif service_type == "GWC":
            service_type = "WMS"
            kvp = {
                "SERVICE":"WMS",
                "REQUEST":"GetMap",
                "VERSION":service_version,
                "SRSNAME":self.crs,
                "LAYERS":self.identifier,
                ("SRS","CRS"):"EPSG:4326",
                "WIDTH":1024,
                "HEIGHT":1024,
                "FORMAT":"image/png"
            }
            if not bbox:
                #bbox is null,use australian bbox
                bbox = [108.0000, -45.0000, 155.0000, -10.0000]
            #compute the tile which can cover the whole bbox
            tile_size = max([bbox[2] - bbox[0],bbox[3] - bbox[1]])
            max_tiles = int(180 / tile_size)
            max_level = -1
            tile_bbox = None
            while (max_tiles > 0):
                max_tiles /= 2
                max_level += 1
            while(max_level >= 0):
                degreePerTile = 180.0 / math.pow(2,max_level)
                xtile = int((bbox[0] + 180) / degreePerTile)
                ytile = int((bbox[1] + 90) / degreePerTile)
                tile_bbox = [xtile * degreePerTile - 180,ytile * degreePerTile - 90,(xtile + 1) * degreePerTile - 180,(ytile + 1) * degreePerTile - 90]
                if tile_bbox[0] <= bbox[0] and tile_bbox[1] <= bbox[1] and tile_bbox[2] >= bbox[2] and tile_bbox[3] >= bbox[3]:
                    break
                else:
                    max_level -= 1
                    tile_bbox = None
                tile_bbox = []
            if not tile_bbox:
                tile_bbox = [0,-90,180,90]

            kvp["BBOX"] = bbox2str(tile_bbox,service_type,service_version)
        else:
            raise Exception("Unknown service type({})".format(service_type))

        endpoint = endpoint.strip()
        if endpoint[-1] in ("?","&"):
            base_url = endpoint
        elif '?' in endpoint:
            base_url = '{0}&'.format(endpoint)
        else:
            base_url= '{0}?'.format(endpoint)

        base_url_upper = base_url.upper()

        is_exist = lambda k: any([ any([base_url_upper.find(s) >= 0 for s in ["&{}=".format(n.upper()),"?{}=".format(n.upper())]]) for n in (k if isinstance(k,tuple) or isinstance(k,list) else [k])])
        
        querystring = "&".join(["{}={}".format(k[0] if isinstance(k,tuple) or isinstance(k,list) else k,v) for k,v in kvp.iteritems() if not is_exist(k)  ])
        link = base_url + querystring

        schema =  '{{"protocol":"OGC:{0}","linkage":"{1}","version":"{2}"}}'.format(service_type.upper(),base_url,service_version)
        return 'None\tNone\t{0}\t{1}'.format(schema,link)


    @staticmethod
    def generate_style_link(style):
        schema =  '{{"protocol":"application/{0}","name":"{1}","default":"{2}","linkage":"{3}/media/"}}'.format(style.format.lower(),style.name,style.default,settings.BASE_URL)
        return 'None\tNone\t{0}\t{1}/media/{2}'.format(schema,settings.BASE_URL,style.content)

    @staticmethod
    def update_links(resources,record):
        pos = 1
        links = ''
        for r in resources:
            r = r.replace('"','\'')
            if pos == 1:
                links += r
            else:
                links += '^{0}'.format(r)
            pos += 1
        record.links = links
        record.save()

    @property
    def width(self):
        return self._calculate_from_bbox('width')

    @property
    def height(self):
        return self._calculate_from_bbox('height')

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
def update_links(sender, instance, **kwargs):
    link = Record.generate_style_link(instance)
    links_parts = re.split("\t",link)
    json_link = json.loads(links_parts[2])
    present = False
    style_links = instance.record.style_links
    ows_links = instance.record.ows_links
    if not instance.record.links:
        instance.record.links = ''
    for link in style_links:
        parts = re.split("\t",link)
        r = json.loads(parts[2].replace("'","\""))
        if r['name'] == json_link['name'] and r['protocol'] == json_link['protocol']:
            present = True
    if not present:
        style_links.append(link)
        links = ows_links + style_links
        Record.update_links(links,instance.record)

@receiver(post_delete,sender=Style)
def remove_style_links(sender, instance, **kwargs):
    style_links = instance.record.style_links
    ows_links = instance.record.ows_links
    #remote deleted style's link
    for link in style_links:
        parts = re.split("\t",resource)
        r = json.loads(parts[2].replace("'","\""))
        if r['name'] == instance.name and instance.format.lower() in r['protocol']:
            style_links.remove(link)

    links = ows_links + style_links
    Record.update_links(links,instance.record)

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


