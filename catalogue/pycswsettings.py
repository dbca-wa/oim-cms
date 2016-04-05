"""
Build pycsw settings
"""
import os.path

from django.core.urlresolvers import reverse
from django.conf import settings
from django.apps import apps

from .models import PycswConfig


def build_pycsw_settings(app=None):
    record_table = "public.catalogue_record"
    config = PycswConfig.objects.first()
    if app:
        url = "{}{}".format(settings.BASE_URL,
                reverse("csw_app_endpoint",kwargs={"app":app or ""}))
    else:
        url = "{}{}".format(settings.BASE_URL,
                reverse("csw_endpoint"))
    poc = config.point_of_contact
    org = poc.organization
    django_db = settings.DATABASES["default"]
    db_connection = {
        "django.db.backends.sqlite3": "sqlite:///{}".format(django_db["NAME"]),
        "django.contrib.gis.db.backends.postgis":
        "postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}".format(USER=django_db.get("USER") or "anonymous",PASSWORD=django_db.get("PASSWORD") or "",HOST=django_db.get("HOST") or "127.0.0.1",PORT=django_db.get("PORT") or "5432" ,NAME=django_db["NAME"])
    }.get(django_db["ENGINE"])
    mappings_path = os.path.join(apps.get_app_config("catalogue").path,
                                 "mappings.py")
    # the values must be strings because PYCSW will feed this dict
    # to a SafeConfigParser
    pycsw_settings = {
        "server": {
            "home": settings.BASE_DIR,
            "url": url,
            "mimetype": "application/xml; charset=UTF-8",
            "encoding": "UTF-8",
            "language": "en-US",
            "maxrecords": str(config.max_records),
            #"loglevel": "DEBUG",
            #"logfile": "/tmp/pycsw.log",
            #"ogc_schemas_base": "http://foo",
            #"federatedcatalogues": "http://catalog.data.gov/csw",
            #"pretty_print": "true",
            #"gzip_compresslevel": "8",
            #"domainquerytype": "range",
            #"domaincounts": "true",
            #"spatial_ranking": "true",
            "profiles": "apiso",
        },
        "manager": {
            "transactions": "true" if config.transactions else "false",
            "allowed_ips": config.allowed_ips,
            #"csw_harvest_pagesize": "10",
        },
        "metadata:main": {
            "identification_title": config.title,
            "identification_abstract": config.abstract,
            "identification_keywords": config.keywords,
            "identification_keywords_type": config.keywords_type,
            "identification_fees": config.fees,
            "identification_accessconstraints": config.access_constraints,
            "provider_name": org.name,
            "provider_url": org.url,
            "contact_name": poc.name,
            "contact_position": poc.position,
            "contact_address": org.address,
            "contact_city": org.city,
            "contact_stateorprovince": org.state_or_province,
            "contact_postalcode": org.postal_code,
            "contact_country": org.country,
            "contact_phone": poc.phone,
            "contact_fax": poc.fax,
            "contact_email": poc.email,
            "contact_url": poc.url,
            "contact_hours": poc.hours_of_service,
            "contact_instructions": poc.contact_instructions,
            "contact_role": "pointOfContact",
        },
        "repository": {
            # sqlite
            "database": db_connection,
            # postgres
            #"database": "postgresql://username:password@localhost/pycsw",
            # mysql
            #"database": "mysql://username:password@localhost/pycsw?charset=utf8",
            "mappings": mappings_path,
            "table": record_table,
        },
        "metadata:inspire": {
            "enabled": "true" if config.inspire_enabled else "false",
        },
    }
    if config.repository_filter != "":
        pycsw_settings["repository"]["filter"] = config.repository_filter
    if config.inspire_enabled:
        inspire = pycsw_settings["metadata:inspire"]
        inspire["languages_supported"] = config.inspire_languages,
        inspire["default_language"] = config.inspire_default_language,
        inspire["date"] = config.inspire_date.isoformat(),
        inspire["gemet_keywords"] = config.gemet_keywords,
        inspire["conformity_service"] = config.conformity_service,
        inspire["contact_name"] = poc.name,
        inspire["contact_email"] = poc.email,
        inspire["temp_extent"] = "{}/{}".format(
            config.temporal_extent_start.isoformat(),
            config.temporal_extent_end.isoformat()),
    return pycsw_settings
