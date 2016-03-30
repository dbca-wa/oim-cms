from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.contrib.sites.shortcuts import get_current_site
from lxml import etree
from pycsw.server import Csw

from .pycswsettings import build_pycsw_settings

import logging


logger = logging.getLogger(__name__)


class CswEndpoint(View):

    def get(self, request):
        pycsw_settings = build_pycsw_settings(request.get('app',None))
        server = Csw(rtconfig=pycsw_settings, env=request.META.copy())
        server.request = "http://{}{}".format(get_current_site(request),
                                              reverse("csw_endpoint"))
        server.requesttype = request.method
        server.kvp = self._normalize_params(request.GET)
        response = server.dispatch()
        return HttpResponse(response, content_type="application/xml")

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CswEndpoint, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        pycsw_settings = build_pycsw_settings()
        server = Csw(rtconfig=pycsw_settings, env=request.META.copy(),
                     version=self._get_post_version(request.body))
        logger.info(request.body)
        server.request = request.body
        server.requesttype = request.method
        status_code, response = server.dispatch()
        return HttpResponse(response, status=status_code,
                            content_type="application/xml")

    # TODO - Remove this method once pycsw mainlines the pending pull request
    def _normalize_params(self, query_dict):
        """
        A hack to overcome PyCSW's early normalizing of KVP args.

        Since PyCSW normalizes KVP args in the server.dispatch_cgi() and
        server.dispatch_wsgi() methods, we need to explicitly do the same
        here, as we are bypassing these methods and calling server.dispatch()
        """

        kvp = dict()
        for k, v in query_dict.iteritems():
            kvp[k.lower()] = v
        return kvp

    def _get_post_version(self, raw_request):
        exml = etree.fromstring(raw_request)
        return exml.get("version")


