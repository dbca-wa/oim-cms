from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.core import urls as wagtail_urls

from core import views

admin.site.site_header = 'OIM CMS Database Administration'

urlpatterns = [
    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('django-admin/', admin.site.urls),
    re_path(r'^draft/(?P<path>.*)', views.draft, name='draft'),
    path('search', views.search, name='search'),
    path('redirect/', views.redirect, name='redirect'),
    path('', include(wagtail_urls)),
]

if settings.DEBUG:  # Serve media locally in development.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.error404
