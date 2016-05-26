from django.contrib.gis import admin
import models

@admin.register(models.Room)
class RoomAdmin(admin.OSMGeoAdmin):
    list_display = ('name','channel','owner')
    readonly_fields = ('modified','channel')
    fieldsets = (
        ('', {
            'fields' :("name","channel","owner","o365_group","link","modified","geom", "centre","extent")
        }),
    )