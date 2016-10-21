from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls

from approvals import urls as approvals_urls
from catalogue import urls as catalogue_urls
from core import views
from oim_cms.api import api_urlpatterns

admin.site.site_header = 'OIM CMS Database Administration'

urlpatterns = [
    url(r'^approvals/', include(approvals_urls)),
    url(r'^catalogue/', include(catalogue_urls)),
    url(r'^django-admin/', include(admin.site.urls)),
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),
    url(r'^forms/', views.forms, name='forms'),
    url(r'^api/', include(api_urlpatterns)),
    url(r'^draft/(?P<path>.*)', views.draft, name='draft'),
    url(r'^search', views.search, name='search'),
    url(r'^logout', views.logout_view, name='logout'),
    url(r'^redirect/', views.redirect, name='redirect'),
    url(r'^auth$', views.auth, name='auth'),
    url(r'^auth_ip$', views.auth_ip, name='auth_ip'),
    url(r'^auth_get$', views.auth_get, name='auth_get'),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    url(r'', include('django.contrib.auth.urls', namespace='auth')),
    url(r'', include(wagtail_urls)),
]

if settings.DEBUG:  # Serve media locally in development.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.error404
