from __future__ import unicode_literals, absolute_import
from django.conf.urls import url
from .views import (
    AddressBook, UserAccounts, ITSystemRegister, ITSystemDetail,
    ITSystemUpdate,
    itsystemreq, ITSystemObj, PeopleObj, SaveITSystemRequest)


urlpatterns = [
    url(r'^address-book/$', AddressBook.as_view(), name='km_address_book'),
    url(r'^user-accounts/$', UserAccounts.as_view(), name='km_user_accounts'),
    url(r'^it-systems/$', ITSystemRegister.as_view(), name='km_itsystem_register'),
    url(r'^it-systems/(?P<system_id>S\d+)/$', ITSystemDetail.as_view(), name='km_itsystem_detail'),
    url(r'^it-systems/(?P<system_id>S\d+)/update/$', ITSystemUpdate.as_view(), name='km_itsystem_update'),
    # ==================================================
    # Legacy views below.
    # ==================================================
    url(r'^it-system/update/$', itsystemreq, name='km_itsystem_update'),
    url(r'^itsystemreq/$', ITSystemObj, name='km_itsystem'),
    url(r'^peoplelist/$', PeopleObj, name='km_peoplelist'),
    url(r'^saveitreq/$', SaveITSystemRequest, name='api_saveitreq')
]
