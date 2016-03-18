from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from api import RecordViewSet
from . import views

router = routers.DefaultRouter()
router.register(r'api',RecordViewSet)

urlpatterns = [
    url(r'^$', views.CswEndpoint.as_view(), name="csw_endpoint"),
    url(r'^', include(router.urls))
]
