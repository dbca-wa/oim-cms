from __future__ import unicode_literals, absolute_import
from django.conf.urls import url
from .views import AddressBook, UserAccounts, NewUserForm


urlpatterns = [
    url(r'^address-book/', AddressBook.as_view(), name='km_address_book'),
    url(r'^user-accounts/', UserAccounts.as_view(), name='km_user_accounts'),
    url(r'^new-user/', NewUserForm.as_view(), name='new_user_form'),
]
