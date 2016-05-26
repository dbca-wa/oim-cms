from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers
from api import RoomViewSet
from . import views

router = routers.DefaultRouter()
router.register(r'^rooms',RoomViewSet)

api_patterns = [
    url(r'^', include(router.urls))
]

urlpatterns = [
    url(r'^api/', include(api_patterns)),
]
