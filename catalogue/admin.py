import json
import sys
import traceback

from django.contrib import admin
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.conf import settings
from django.template import Context, Template

from dpaw_utils import requests

from . import models
from .forms import RecordForm,StyleForm,ApplicationForm


class CollaboratorInline(admin.StackedInline):
    model = models.Collaborator
    extra = 1
    
class StyleInline(admin.StackedInline):
    model = models.Style
    extra = 1
    form = StyleForm
    template = "catalogue/style/edit_inline/stacked.html"
    
#@admin.register(models.Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ('name','record','format','default')
    form = StyleForm
    
    def has_delete_permission(self, request, obj=None):
        """
        Only want to hide the delete button(link) in the edit page
        """
        if request.path == "/django-admin/catalogue/style/":
            #request the list page
            return super(StyleAdmin,self).has_delete_permission(request,obj)
        elif obj and obj.name == models.Style.BUILTIN:
            # request the edit page and the style is a builtin style
            return False
        else:
            return super(StyleAdmin,self).has_delete_permission(request,obj)

    def custom_delete_selected(self,request,queryset):
        if request.POST.get('post') != 'yes':
            #the confirm page, or user not confirmed
            return self.default_delete_action[0](self,request,queryset)
    
        #user confirm to delete the publishes, execute the custom delete logic.
        result = None
        failed_objects = []

        for style in queryset:
            try:
                style.delete()
            except:
                error = sys.exc_info()
                failed_objects.append((style.identifier,traceback.format_exception_only(error[0],error[1])))
                #remove failed, continue to process the next publish
                continue

        if failed_objects:
            messages.warning(request, mark_safe("Some selected styles are deleted failed:<ul>{0}</ul>".format("".join(["<li>{0} : {1}</li>".format(o[0],o[1]) for o in failed_objects]))))
        else:
            messages.success(request, "All selected styles are deleted successfully")

    def get_actions(self, request):
        actions = super(StyleAdmin, self).get_actions(request)
        self.default_delete_action = actions['delete_selected']
        del actions['delete_selected']
        actions['delete_selected'] = (StyleAdmin.custom_delete_selected,self.default_delete_action[1],self.default_delete_action[2])
        return actions 

    
@admin.register(models.Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("identifier","service_type","crs","title", "auto_update","active","modified","publication_date")
    inlines = [StyleInline,]
    readonly_fields = ('service_type','service_type_version','crs','_bounding_box',"_ows_resources",'active','publication_date','modified','insert_date')
    search_fields = ["identifier",'service_type']
    form = RecordForm
    """
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('identifier',)
        return self.readonly_fields
    """
    html = """<table>
<tr>
    <th style='width:100px;border-bottom:None'>Min X</th>
    <th style='width:100px;border-bottom:None'>Min Y</th>
    <th style='width:100px;border-bottom:None'>Max X</th>
    <th style='width:100px;border-bottom:None'>Max Y</th>
</tr>
<tr>
    <td style='border-bottom:None'>{}</td>
    <td style='border-bottom:None'>{}</td>
    <td style='border-bottom:None'>{}</td>
    <td style='border-bottom:None'>{}</td>
</tr>
</table>
"""
    def _bounding_box(self,instance):
        bounding_box = ["-","-","-","-"]
        if instance.bounding_box:
            bounding_box = instance.bbox or ["-","-","-","-"]

        return self.html.format(*bounding_box)

    _bounding_box.allow_tags = True
    _bounding_box.short_description = "bounding_box"

    ows_resources_template  = """<table>
<tr>
    <th style='width:100px;border-bottom:None'>Service Type</th>
    <th style='width:100px;border-bottom:None'>Version</th>
    <th style='border-bottom:None'>Endpoint</th>
    <th style='width:100px;border-bottom:None'>Preview</th>
</tr>
{% for resource in resources %}
<tr>
    <td style='border-bottom:None'>{{resource.type}}</td>
    <td style='border-bottom:None'>{{resource.version}}</td>
    <td style='border-bottom:None'>{{resource.endpoint}}</td>
    <td style='border-bottom:None'><A target='_blank' href='{{resource.link}}'>preview</A></td>
</tr>
{% endfor %}
</table>
"""
    def _ows_resources(self,instance):
        resources = ""
        ows_resources = instance.ows_resource
        if ows_resources:
            context = Context({"resources": ows_resources})
            resources =  Template(self.ows_resources_template).render(context)

        return resources

    _ows_resources.allow_tags = True
    _ows_resources.short_description = "OWS Resources"


    def get_inline_instances(self, request, obj=None):
        if obj and obj.service_type == "WMS":
            return []
        else:
            return super(RecordAdmin,self).get_inline_instances(request,obj)

    def has_add_permission(self,request):
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Only want to hide the delete button(link) in the edit page
        """
        if request.path == "/django-admin/catalogue/record/":
            #request the list page
            return super(RecordAdmin,self).has_delete_permission(request,obj)
        elif obj and obj.active:
            # request the edit page and the record is active
            return False
        else:
            return super(RecordAdmin,self).has_delete_permission(request,obj)

    def publish(self,request,queryset):
        result = None
        failed_objects = []
        data = {"layers":[]}
        for record in queryset:
            data["layers"].append(record.identifier)

        res = None
        try:
            res = requests.post(request,"{}/api/metajobs/".format(settings.BORG_URL),json=data)
            res.raise_for_status()
            result = res.json()
            if result["status"]:
                messages.success(request, "All selected records are published successfully")
            else:
                for layer,status in result.iteritems():
                    if layer == "status": continue
                    if status["status"]: continue
                    failed_objects.append((layer,status["message"]))
                if failed_objects:
                    messages.warning(request, mark_safe("Some selected records are published failed:<ul>{0}</ul>".format("".join(["<li>{0} : {1}</li>".format(o[0],o[1]) for o in failed_objects]))))
                else:
                    messages.success(request, "All selected records are published successfully")

        except Exception as e:
            traceback.print_exc()
            messages.warning(request, str(e))
    publish.short_description = "Publish"


    def custom_delete_selected(self,request,queryset):
        if request.POST.get('post') != 'yes':
            #the confirm page, or user not confirmed
            return self.default_delete_action[0](self,request,queryset)
    
        #user confirm to delete the publishes, execute the custom delete logic.
        result = None
        failed_objects = []

        for record in queryset:
            try:
                record.delete()
            except:
                error = sys.exc_info()
                failed_objects.append((record.identifier,traceback.format_exception_only(error[0],error[1])))
                #remove failed, continue to process the next publish
                continue

        if failed_objects:
            messages.warning(request, mark_safe("Some selected records are deleted failed:<ul>{0}</ul>".format("".join(["<li>{0} : {1}</li>".format(o[0],o[1]) for o in failed_objects]))))
        else:
            messages.success(request, "All selected records are deleted successfully")

    actions = ["publish"]
    def get_actions(self, request):
        actions = super(RecordAdmin, self).get_actions(request)
        self.default_delete_action = actions['delete_selected']
        del actions['delete_selected']
        actions['delete_selected'] = (RecordAdmin.custom_delete_selected,self.default_delete_action[1],self.default_delete_action[2])
        return actions 

@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name","_address","url")
    inlines = [CollaboratorInline,]
    actions = None

    def _address(self,instance):

        return "{0}, {1} {2} {3}, {4} ".format(instance.address or "", instance.city or "",instance.state_or_province or "",instance.postal_code or "" ,instance.country or "")

    _address.short_description = "address"

    def has_add_permission(self,request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.PycswConfig)
class PycswConfigAdmin(admin.ModelAdmin):
    list_display = ("title","language","point_of_contact","inspire_enabled","transactions")

    actions = None

    #def has_add_permission(self, request):
    #    return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self,request):
        return False


class ApplicationLayerInline(admin.TabularInline):
    model = models.ApplicationLayer
    extra = 3
    
@admin.register(models.Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("name","description","last_modify_time","create_time")
    inlines = [ApplicationLayerInline,]
    readonly_fields = ('last_modify_time','create_time')
    form = ApplicationForm
    search_fields = ["name"]
