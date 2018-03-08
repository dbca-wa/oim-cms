from __future__ import unicode_literals, absolute_import
from django.views.generic import TemplateView


class AddressBook(TemplateView):
    template_name = 'knowledge/address_book.html'


class UserAccounts(TemplateView):
    template_name = 'knowledge/user_accounts.html'
