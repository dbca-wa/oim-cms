from django.urls import re_path
from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.core import urls as wagtail_urls

from core import views

admin.site.site_header = 'OIM CMS Database Administration'

urlpatterns = [
    re_path(r'^admin/', include(wagtailadmin_urls)),
    re_path(r'^documents/', include(wagtaildocs_urls)),
    url(r'^django-admin/', admin.site.urls),
    #url(r'^admin/uwsgi/', include('django_uwsgi.urls')),
    #url(r'', include('django.contrib.auth.urls', namespace='auth')),
    url(r'^draft/(?P<path>.*)', views.draft, name='draft'),
    url(r'^search', views.search, name='search'),
    url(r'^logout', views.logout_view, name='logout'),
    url(r'^redirect/', views.redirect, name='redirect'),
    url(r'^auth$', views.auth, name='auth'),
    url(r'^auth_dual$', views.auth_dual, name='auth_dual'),
    url(r'^auth_ip$', views.auth_ip, name='auth_ip'),
    url(r'^auth_get$', views.auth_get, name='auth_get'),
    url(r'', include('social_django.urls', namespace='social')),
    re_path(r'', include(wagtail_urls)),
]

if settings.DEBUG:  # Serve media locally in development.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.error404
