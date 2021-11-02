from django.http import HttpResponse, HttpResponseServerError
from django.utils.deprecation import MiddlewareMixin
from wagtail.core.models import Site
import logging


LOGGER = logging.getLogger("healthcheck")


try:
    from django.conf import settings
    XS_SHARING_ALLOWED_ORIGINS = settings.XS_SHARING_ALLOWED_ORIGINS
    XS_SHARING_ALLOWED_METHODS = settings.XS_SHARING_ALLOWED_METHODS
    XS_SHARING_ALLOWED_HEADERS = settings.XS_SHARING_ALLOWED_HEADERS
    XS_SHARING_ALLOWED_CREDENTIALS = settings.XS_SHARING_ALLOWED_CREDENTIALS
except AttributeError:
    XS_SHARING_ALLOWED_ORIGINS = '*'
    XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']
    XS_SHARING_ALLOWED_HEADERS = ['Content-Type', '*']
    XS_SHARING_ALLOWED_CREDENTIALS = 'true'


class SiteMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """
        Set request.site to contain the Site object responsible for handling this request.
        """
        try:
            request.site = Site.find_for_request(request)
        except Site.DoesNotExist:
            request.site = None


class XsSharing(object):
    """
    This middleware allows cross-domain XHR using the HTML5 postMessage API.

    Access-Control-Allow-Origin: http://foo.example
    Access-Control-Allow-Methods: POST, GET, OPTIONS, PUT, DELETE

    Based off https://gist.github.com/426829
    """
    def process_request(self, request):
        if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META:
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = XS_SHARING_ALLOWED_ORIGINS
            response['Access-Control-Allow-Methods'] = ",".join(XS_SHARING_ALLOWED_METHODS)
            response['Access-Control-Allow-Headers'] = ",".join(XS_SHARING_ALLOWED_HEADERS)
            response['Access-Control-Allow-Credentials'] = XS_SHARING_ALLOWED_CREDENTIALS
            return response

        return None

    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = XS_SHARING_ALLOWED_ORIGINS
        response['Access-Control-Allow-Methods'] = ",".join(XS_SHARING_ALLOWED_METHODS)
        response['Access-Control-Allow-Headers'] = ",".join(XS_SHARING_ALLOWED_HEADERS)
        response['Access-Control-Allow-Credentials'] = XS_SHARING_ALLOWED_CREDENTIALS

        return response


class HealthCheckMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET":
            if request.path == "/readiness":
                return self.readiness(request)
            elif request.path == "/liveness":
                return self.liveness(request)
        return self.get_response(request)

    def liveness(self, request):
        """Returns that the server is alive.
        """
        return HttpResponse("OK")

    def readiness(self, request):
        """Connect to each database and do a generic standard SQL query
        that doesn't write any data and doesn't depend on any tables
        being present.
        """
        try:
            from django.db import connections
            for name in connections:
                cursor = connections[name].cursor()
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if row is None:
                    return HttpResponseServerError("db: invalid response")
        except Exception as e:
            LOGGER.exception(e)
            return HttpResponseServerError("db: cannot connect to database.")

        return HttpResponse("OK")
