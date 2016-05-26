from django.conf.urls import include, url, handler404
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

from core import views
from oim_cms import api

#from catalogue import urls as catalogue_urls
from rooms import urls as room_urls

admin.site.site_header = 'OIM CMS Database Administration'

api_patterns = [
    url(r'^freshdesk', api.freshdesk, name="api_freshdesk"),
    url(r'^ec2_instances', include(api.EC2InstanceResource.urls())),
    url(r'^itsystems', include(api.ITSystemResource.urls())),
    url(r'^itsystems.csv', api.ITSystemResource.as_csv),
    url(r'^mudmaps', include(api.MudMapResource.urls())),
    url(r'^mudmaps.csv', api.MudMapResource.as_csv),
    url(r'^locations', include(api.LocationResource.urls())),
    url(r'^locations.csv', api.LocationResource.as_csv),
    url(r'^devices', include(api.HardwareResource.urls())),
    url(r'^users', include(api.UserResource.urls())),
    url(r'^profile', api.profile),
    url(r'^options', include(api.OptionResource.urls())),
    url(r'^whoami', api.whoamiResource.as_detail(), name="api_whoami"),
]

urlpatterns = [
    url(r'^rooms/', include(room_urls)),
    #url(r'^catalogue/', include(catalogue_urls)),
    url(r'^django-admin/', include(admin.site.urls)),

    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^draft/(?P<path>.*)', views.draft, name='draft'),
    url(r'^search', views.search, name='search'),
    url(r'^logout', views.logout_view, name='logout'),
    url(r'^documents/', include(wagtaildocs_urls)),

    url(r'^api/', include(api_patterns)),
    url(r'^api/{}/'.format(settings.API_SECRET), include(api_patterns)),

    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'', include('django.contrib.auth.urls', namespace='auth')),
    url(r'', include(wagtail_urls)),

    url(r'^redirect/', views.redirect, name='redirect'),
    url(r'^auth$', views.auth, name='auth'),
    url(r'^auth_ip$', views.auth_ip, name='auth_ip'),
    url(r'^pusher/auth$', views.auth_pusher, name='auth_pusher'),
    url(r'^pusher/publish$', views.pusher_publish, name='pusher_publish'),
]

if settings.DEBUG:  # Serve media locally in development.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.error404
