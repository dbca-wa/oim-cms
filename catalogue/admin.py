import json

from django.contrib import admin

from . import models
from .forms import RecordForm


class CollaboratorInline(admin.StackedInline):
    model = models.Collaborator
    extra = 1
    
class StyleInline(admin.StackedInline):
    model = models.Style
    extra = 1
    
@admin.register(models.Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ('name','record','format',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('name',)
        return self.readonly_fields
    
    
@admin.register(models.Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("identifier","service_type","crs","title", "auto_update","modified")
    inlines = [StyleInline,]
    readonly_fields = ('service_type','service_type_version','crs','_bounding_box','publication_date','modified','insert_date')
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
            try:
                bounding_box = json.loads(instance.bounding_box)
                if not bounding_box or not isinstance(bounding_box,list) or len(bounding_box) != 4:
                    bounding_box = ["-","-","-","-"]
            except:
                bounding_box = ["-","-","-","-"]

        return self.html.format(*bounding_box)

    _bounding_box.allow_tags = True
    _bounding_box.short_description = "bounding_box"

            

@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = [CollaboratorInline,]


@admin.register(models.PycswConfig)
class PycswConfigAdmin(admin.ModelAdmin):

    #def has_add_permission(self, request):
    #    return False

    def has_delete_permission(self, request, obj=None):
        return False
