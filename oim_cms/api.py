from django.conf.urls import url
from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer

from core.models import UserSession


class WhoAmIResource(DjangoResource):
    """
    whoami is a read only resource and does not require any request parameters.
    This resource can be used to return the authentication data by whoami request and auth request.
    so only one method 'detail' is required no matter which http method is used.
    """
    http_methods = {
        'list': {
            'GET': 'detail',
            'POST': 'detail',
            'PUT': 'detail',
            'DELETE': 'detail',
        },
        'detail': {
            'GET': 'detail',
            'POST': 'detail',
            'PUT': 'detail',
            'DELETE': 'detail',
        }
    }
    preparer = FieldsPreparer(fields={
        'email': 'user.email',
        'username': 'user.username',
        'first_name': 'user.first_name',
        'last_name': 'user.last_name',
        'shared_id': 'shared_id',
        'session_key': 'session.session_key',
        'client_logon_ip': 'ip'
    })

    def request_body(self):
        return None

    def is_authenticated(self):
        return self.request.user.is_authenticated()

    def detail(self):
        return UserSession.objects.get(
            session__session_key=self.request.session.session_key)


api_urlpatterns = [
    url(r'^whoami', WhoAmIResource.as_detail(), name='api_whoami'),
]
