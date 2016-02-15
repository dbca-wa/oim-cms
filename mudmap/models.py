from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User


class MudMap(models.Model):
    name = models.CharField(max_length=256, unique=True)
    user = models.ForeignKey(User)
    last_saved = models.DateTimeField()
    geojson = JSONField()


class MudMapFeature(models.Model):
    size = models.FloatField(null=True)
    label = models.CharField(max_length=256, null=True)
    colour = models.CharField(max_length=256, null=True)
    mudmap = models.ForeignKey(MudMap, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class MudMapPoint(MudMapFeature):
    wkb_geometry = models.PointField()


class MudMapLineString(MudMapFeature):
    wkb_geometry = models.LineStringField()


class MudMapPolygon(MudMapFeature):
    wkb_geometry = models.PolygonField()
