from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import LocalPropertyRegisterList, LocalPropertyRegisterDetail

urlpatterns = patterns(
    '',
    url(r'^local-property-registers/$', login_required(
        LocalPropertyRegisterList.as_view()), name='lpr_list'),
    url(r'^local-property-registers/(?P<pk>\d+)/$', login_required(
        LocalPropertyRegisterDetail.as_view()), name='lpr_detail'),

)
