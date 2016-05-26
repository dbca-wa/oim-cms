from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.dispatch import receiver
from django.db.models.signals import post_save
from core.views import pusher

class Room(models.Model):
    
    owner = models.ForeignKey('auth.User')
    modified = models.DateTimeField(null=True, blank=True,auto_now=True)
    centre = models.PointField()
    geom = JSONField(null=True, blank=True)
    extent = models.PolygonField()
    o365_group = JSONField(null=True, blank=True)
    name = models.CharField(max_length=128)
    link = models.URLField(null=True,blank=True)
    
    @property
    def channel(self):
        return self.name.lower()
        
    def __unicode__(self):
        return self.name
    
    def send_update(self):
        pusher.trigger(self.channel,'room_update',{'message': json.dumps('New data is available')})
'''
@receiver(post_save,sender=Room)
def send_pusher_message(sender, instance, **kwargs):
    instance.send_update()
'''