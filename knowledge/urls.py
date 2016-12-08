from __future__ import unicode_literals, absolute_import
from django.conf.urls import url
from .views import (
    AddressBook, UserAccounts,
    itsystemreq, ITSystemObj, PeopleObj, SaveITSystemRequest)


urlpatterns = [
    url(r'^address-book/', AddressBook.as_view(), name='km_address_book'),
    url(r'^user-accounts/', UserAccounts.as_view(), name='km_user_accounts'),
    # ==================================================
    # Legacy views below.
    # ==================================================
    url(r'^it-system/update/', itsystemreq, name='km_itsystem_update'),
    url(r'^itsystemreq/', ITSystemObj, name='km_itsystem'),
    url(r'^peoplelist/', PeopleObj, name='km_peoplelist'),
    url(r'^saveitreq/', SaveITSystemRequest, name='api_saveitreq')
]
