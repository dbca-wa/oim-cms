from django.contrib import admin

from . import models


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
    list_display = ("id", "identifier", "title",)
    inlines = [StyleInline,]
    readonly_fields = ('publication_date','modified',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('identifier',)
        return self.readonly_fields


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = [CollaboratorInline,]


@admin.register(models.PycswConfig)
class PycswConfigAdmin(admin.ModelAdmin):

    #def has_add_permission(self, request):
    #    return False

    def has_delete_permission(self, request, obj=None):
        return False
