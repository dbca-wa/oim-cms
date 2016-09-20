from django.conf.urls import url
from .views import ApprovalCreate, ApprovalDetail, ApprovalConfirm


urlpatterns = [
    url(r'^create/$', ApprovalCreate.as_view(), name='approval_create'),
    url(r'^(?P<pk>[0-9]+)/$', ApprovalDetail.as_view(), name='approval_detail'),
    url(r'^confirm/(?P<guid>[^/]+)/$', ApprovalConfirm.as_view(), name='approval_confirm'),
]
