from django.conf.urls import include, url
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.CswEndpoint.as_view(), name="csw_endpoint")
]
