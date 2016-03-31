from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from api import RecordViewSet
from . import views

router = routers.DefaultRouter()
router.register(r'^records',RecordViewSet)

api_patterns = [
    url(r'^', include(router.urls))
]

urlpatterns = [
    url(r'^api/', include(api_patterns)),
    url(r'^$', views.CswEndpoint.as_view(), name="csw_endpoint"),
    url(r'^(?P<app>[a-z0-9_]*)/$', views.CswEndpoint.as_view(), name="csw_app_endpoint"),
]
