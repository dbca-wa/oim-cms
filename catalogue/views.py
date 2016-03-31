from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.contrib.sites.shortcuts import get_current_site
from lxml import etree
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Integer
from sqlalchemy.schema import Column
from sqlalchemy import inspection,log,util
from sqlalchemy.sql import util as sql_util
from sqlalchemy.orm.mapper import Mapper as BaseMapper
from pycsw.server import Csw
from itertools import chain
from .models import Application

from .pycswsettings import build_pycsw_settings

import logging


logger = logging.getLogger(__name__)

@inspection._self_inspects
@log.class_logger
class Mapper(BaseMapper):
    def _configure_pks(self):
        self.tables = sql_util.find_tables(self.mapped_table)

        self._pks_by_table = {}
        self._cols_by_table = {}

        all_cols = util.column_set(chain(*[
            col.proxy_set for col in
            self._columntoproperty]))

        pk_cols = util.column_set(c for c in all_cols if c.primary_key)
        # identify primary key columns which are also mapped by this mapper.
        tables = set(self.tables + [self.mapped_table])
        self._all_tables.update(tables)
        self._cols_by_table[self.mapped_table] = all_cols
        primary_key = [c for c in all_cols if c.name in self._primary_key_argument]
        self._pks_by_table[self.mapped_table] = primary_key

        self.primary_key = tuple(primary_key)
        self._log("Identified primary key columns: %s", primary_key)

        # determine cols that aren't expressed within our tables; mark these
        # as "read only" properties which are refreshed upon INSERT/UPDATE
        self._readonly_props = set(
            self._columntoproperty[col]
            for col in self._columntoproperty
            if self._columntoproperty[col] not in self._identity_key_props and
            (not hasattr(col, 'table') or
                col.table not in self._cols_by_table))

class CswEndpoint(View):
    application_records = {}
    def get(self, request,app=None):
        record_table = Application.get_view_name(app) if app else "catalogue_record"
        pycsw_settings = build_pycsw_settings()
        server = Csw(rtconfig=pycsw_settings, env=request.META.copy())
        if app:
            #request by named app, use app related view
            try:
                if not self.application_records.get(app,None):
                    base = declarative_base(bind=server.repository.engine,mapper=Mapper)
                    self.application_records[app] = type('dataset', (base,),
                            dict(__tablename__=record_table,__table_args__={'autoload': True,'schema': None},__mapper_args__={"primary_key":["id"]}))
                server.repository.dataset = self.application_records[app]
            except:
                pass

        server.request = "http://{}{}".format(get_current_site(request),
                                              reverse("csw_endpoint"))
        server.requesttype = request.method
        server.kvp = self._normalize_params(request.GET)
        response = server.dispatch()
        return HttpResponse(response, content_type="application/xml")

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CswEndpoint, self).dispatch(request, *args, **kwargs)

    def post(self, request,app=None):
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


