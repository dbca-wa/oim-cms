from babel.dates import format_timedelta
from django.conf import settings
from django.db.models import F
from django.http import (
    HttpResponseRedirect, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest)
from django.utils.text import slugify
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from djqscsv import render_to_csv_response
import itertools
import json
from mptt.templatetags.mptt_tags import cache_tree_children
import requests
from restless.utils import MoreTypesJSONEncoder
from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer
from restless.resources import skip_prepare

from core.models import UserSession
from mudmap.models import MudMap
from registers.models import (
    CostCentre, ITSystem, Hardware, OrgUnit, Location, SecondaryLocation)
from tracking.models import DepartmentUser, EC2Instance


def format_fileField(request, value):
    if value:
        return request.build_absolute_uri(
            "{}{}".format(settings.MEDIA_URL, value))
    else:
        return value


class FieldsFormatter(object):
    """
    A formatter object to format specified fields with cofigured formatter object.

    This takes a
        ``request`` parameter , a http request object
        ``formatters`` parameter: a dictionary of keys (a dotted lookup path to
        the desired attribute/key on the object) and values(a formatter object).

    for propertis without a configed formatter method, return the raw value directly.

    This method will replace the old value with formatted value.

    Example::

        preparer = FieldsFormatter(request,fields={
            # ``user`` is the key the client will see.
            # ``author.pk`` is the dotted path lookup ``FieldsPreparer``
            # will traverse on the data to return a value.
            'photo': format_fileField,
        })

    """

    def __init__(self, formatters):
        super(FieldsFormatter, self).__init__()
        self._formatters = formatters

    def format(self, request, data):
        """
        format data with configured formatter object
        data can be a list or a single object
        """
        if data:
            if isinstance(data, list):
                # list object
                for row in data:
                    self.format_object(request, row)
            else:
                # a single object
                self.format_object(request, data)

        return data

    def format_object(self, request, data):
        """
        format a simgle object.

        Uses the ``lookup_data`` method to traverse dotted paths.

        Replace the value with formatted value, if required.

        """
        if not self._formatters:
            # No fields specified. Serialize everything.
            return data

        for lookup, formatter in self._formatters.items():
            if not formatter:
                continue
            data = self.format_data(request, lookup, data, formatter)

        return data

    def format_data(self, request, lookup, data, formatter):
        """
        Given a lookup string, attempts to descend through nested data looking for
        the value ,format the value and then replace the old value with formatted value.

        Can work with either dictionary-alikes or objects (or any combination of
        those).

        Lookups should be a string. If it is a dotted path, it will be split on
        ``.`` & it will traverse through to find the final value. If not, it will
        simply attempt to find either a key or attribute of that name & return it.

        Example::

            >>> data = {
            ...     'type': 'message',
            ...     'greeting': {
            ...         'en': 'hello',
            ...         'fr': 'bonjour',
            ...         'es': 'hola',
            ...     },
            ...     'person': Person(
            ...         name='daniel'
            ...     )
            ... }
            >>> lookup_data('type', data)
            'message'
            >>> lookup_data('greeting.en', data)
            'hello'
            >>> lookup_data('person.name', data)
            'daniel'

        """
        parts = lookup.split('.')

        if not parts or not parts[0]:
            return formatter(request, data)

        part = parts[0]
        remaining_lookup = '.'.join(parts[1:])

        if hasattr(data, 'keys') and hasattr(data, '__getitem__'):
            # Dictionary enough for us.
            try:
                value = data[part]
                if remaining_lookup:
                    # is an object
                    self.format_data(
                        request, remaining_lookup, value, formatter)
                else:
                    # is a simple type value
                    data[part] = formatter(request, value)
            except:
                # format failed, ignore
                pass
        else:
            try:
                value = getattr(data, part)
                # Assume it's an object.
                if remaining_lookup:
                    # is an object
                    self.format_data(
                        request, remaining_lookup, value, formatter)
                else:
                    # is a simple type value
                    setattr(data, part, formatter(request, value))
            except:
                # format failed, ignore
                pass

        return data


class CSVDjangoResource(DjangoResource):

    @classmethod
    def as_csv(cls, request):
        resource = cls()
        if not hasattr(resource, "list_qs"):
            return HttpResponse(
                "list_qs not implemented for {}".format(cls.__name__))
        resource.request = request
        return render_to_csv_response(
            resource.list_qs(), field_order=resource.VALUES_ARGS)


@csrf_exempt
def freshdesk(request):
    lines = []
    for key, val in request.POST.iteritems():
        if not val:
            val = "(blank)"
        lines.append("<li><b>{}</b>: {}</li>".format(key, val))
    lines.sort()
    description = "<ul>{}</ul>".format("".join(lines))
    ticket = {"helpdesk_ticket": {
        "subject": request.POST.get("subject", "Form submitted"),
        "email": request.user.email,
        "priority": int(request.POST.get("priority", 1)),
        "status": int(request.POST.get("status", 2)),
        "description_html": description,
        "source": 4
    }}
    r = requests.post(settings.FRESHDESK_ENDPOINT + "/helpdesk/tickets.json",
                      auth=settings.FRESHDESK_AUTH, headers={
                          "Content-Type": "application/json"},
                      data=json.dumps(ticket))
    ticket_id = json.loads(r.content)["helpdesk_ticket"]["display_id"]
    return HttpResponseRedirect(
        settings.FRESHDESK_ENDPOINT + "/support/tickets/{}".format(ticket_id))


def recursive_node_to_dict(node):
    # http://stackoverflow.com/questions/12556268/fastest-way-to-create-json-to-reflect-a-tree-structure-in-python-django-using
    result = {
        'name': node.name, 'id': node.pk,
        'children': [recursive_node_to_dict(c) for c in node._cached_children]
    }
    if not result["children"]:
        del result["children"]
    return result


class OptionResource(DjangoResource):

    @skip_prepare
    def list(self):
        return getattr(self, "data_" + self.request.GET["list"])()

    def data_org_structure(self):
        return [recursive_node_to_dict(cache_tree_children(dept.get_descendants(include_self=True))[0])
                for dept in OrgUnit.objects.filter(unit_type=0).order_by('name')]

    def data_cost_centre(self):
        return ["CC{} / {}".format(
            *c) for c in CostCentre.objects.all().values_list("code", "org_position__name")]

    def data_dept_user(self):
        return [u[0] for u in DepartmentUser.objects.filter(
            active=True, email__iendswith=".wa.gov.au").order_by("email").values_list("email")]

    def data_itsystem(self):
        return ["{} {}".format(
            *s) for s in ITSystem.objects.all().values_list("system_id", "name")]

    def data_statuslogin(self):
        return [l[1] for l in list(ITSystem.STATUS_CHOICES) + list(ITSystem.ACCESS_CHOICES) + list(ITSystem.AUTHENTICATION_CHOICES)]

    def data_location(self):
        return [l.name for l in Location.objects.all().order_by('name')]

    def data_division(self):
        return [i.name for i in OrgUnit.objects.filter(unit_type=1).order_by('name')]

    def data_dept(self):
        return [i.acronym for i in OrgUnit.objects.filter(unit_type=0, acronym__gt="").order_by('name')]

    def data_department(self):
        return [i.name for i in OrgUnit.objects.filter(unit_type=0).order_by('name')]

    def data_branch(self):
        return [i.name for i in OrgUnit.objects.filter(unit_type=2).order_by('name')]

    def data_section(self):
        return [i.name for i in OrgUnit.objects.filter(unit_type=7).order_by('name')]

    def data_regiondistrict(self):
        return [i.name for i in OrgUnit.objects.filter(unit_type__in=[3, 6]).order_by('name')]

    def data_office(self):
        return [i.name for i in OrgUnit.objects.filter(unit_type=5).order_by('name')]


class whoamiResource(DjangoResource):
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


class HardwareResource(DjangoResource):
    VALUES_ARGS = (
        "email", "date_updated",
        "computer__hostname",
        "local_info",
        "local_current")

    def is_authenticated(self):
        return True

    @skip_prepare
    def list(self):
        FILTERS = {"computer__isnull": False, "local_info__isnull": False}
        # Only return production apps
        if "hostname" in self.request.GET:
            FILTERS["computer__hostname__istartswith"] = self.request.GET[
                "hostname"]
        if self.request.GET.get("local_current", "").lower() == "false":
            FILTERS["local_current"] = False
        data = list(Hardware.objects.filter(
            **FILTERS).values(*self.VALUES_ARGS))
        for row in data:
            row.update(json.loads(row["local_info"]))
        return data

    @skip_prepare
    def create(self):
        computer = Hardware.objects.get(
            computer__hostname__istartswith=self.data["hostname"])
        local_info = json.dumps(self.data)
        computer.local_info = local_info
        computer.local_current = self.data.get("local_current", False)
        computer.save()
        data = list(
            Hardware.objects.filter(
                pk=computer.pk).values(
                *
                self.VALUES_ARGS))[0]
        data.update(json.loads(data["local_info"]))
        return data


class EC2InstanceResource(CSVDjangoResource):
    VALUES_ARGS = (
        'pk', 'name', 'ec2id', 'launch_time', 'running', 'next_state'
    )

    def is_authenticated(self):
        return True

    def list_qs(self):
        if "ec2id" in self.request.GET:
            return EC2Instance.objects.filter(
                ec2id=self.request.GET["ec2id"]).values(*self.VALUES_ARGS)
        else:
            return EC2Instance.objects.exclude(
                running=F("next_state")).values(*self.VALUES_ARGS)

    @skip_prepare
    def list(self):
        data = list(self.list_qs())
        return data

    @skip_prepare
    def create(self):
        if not isinstance(self.data, list):
            self.data = [self.data]
            deleted = None
        else:
            deleted = EC2Instance.objects.exclude(
                ec2id__in=[i["InstanceId"] for i in self.data]).delete()
        for instc in self.data:
            instance, created = EC2Instance.objects.get_or_create(ec2id=instc["InstanceId"])
            instance.name = [x["Value"] for x in instc["Tags"] if x["Key"] == "Name"][0]
            instance.launch_time = instc["LaunchTime"]
            instance.running = instc["State"]["Name"] == "running"
            instance.extra_data = instc
            instance.save()
        return {"saved": len(self.data), "deleted": deleted}


class MudMapResource(CSVDjangoResource):
    VALUES_ARGS = (
        'pk', 'name', 'user', 'last_saved'
    )

    def is_authenticated(self):
        return True
        return self.data.get("name", "").startswith(
            self.request.user.email.lower())

    def list_qs(self):
        # Only return production apps
        FILTERS = {}
        if "mudmap_id" in self.request.GET:
            FILTERS["pk"] = self.request.GET["mudmap_id"]
        return MudMap.objects.filter(**FILTERS).values(*self.VALUES_ARGS)

    @skip_prepare
    def list(self):
        data = list(self.list_qs())
        return data

    @skip_prepare
    def create(self):
        mudmap, created = MudMap.objects.get_or_create(name=self.data["name"])
        if "delete" in self.data:
            mudmap.delete()
            return {"deleted": self.data["name"]}
        else:
            mudmap.geojson = self.data["features"]
            mudmap.lastsave = self.data["lastsave"]
            mudmap.user = self.request.user
            mudmap.save()
            return {"saved": self.data["name"]}


class LocationResource(CSVDjangoResource):
    VALUES_ARGS = (
        'pk', 'name', 'address', 'phone', 'fax', 'email', 'point', 'url', 'bandwidth_url'
    )

    def list_qs(self):
        # Only return production apps
        FILTERS = {}
        if "location_id" in self.request.GET:
            FILTERS["pk"] = self.request.GET["location_id"]
        return Location.objects.filter(**FILTERS).values(*self.VALUES_ARGS)

    @skip_prepare
    def list(self):
        data = list(self.list_qs())
        for row in data:
            if row["point"]:
                row["point"] = row["point"].wkt
        return data


class ITSystemResource(CSVDjangoResource):

    def prepare(self, data):
        """Prepare a custom API response for ITSystemResource objects.
        """
        # Owner > CC > Division > Manager
        cost_centre__division__manager__name = ''
        cost_centre__division__manager__email = ''
        cost_centre__division__manager__title = ''
        cost_centre__division__name = ''
        cost_centre__name = ''
        cost_centre__code = ''
        # Every damn field is nullable!
        if data.owner:
            if data.owner.cost_centre:
                cost_centre__name = data.owner.cost_centre.name
                cost_centre__code = data.owner.cost_centre.code
                if data.owner.cost_centre.division:
                    cost_centre__division__name = data.owner.cost_centre.division.name
                    if data.owner.cost_centre.division.manager:
                        cost_centre__division__manager__name = data.owner.cost_centre.division.manager.name
                        cost_centre__division__manager__email = data.owner.cost_centre.division.manager.email
                        cost_centre__division__manager__title = data.owner.cost_centre.division.manager.title

        domain = self.request.build_absolute_uri().replace(self.request.get_full_path(), '')
        prepped = {
            'pk': data.pk,
            'name': data.name,
            'acronym': data.acronym,
            'system_id': data.system_id,
            'description': data.description,
            'documentation': data.documentation,
            'technical_documentation': data.technical_documentation,
            'authentication_display': data.authentication_display or '',
            'access_display': data.access_display or '',
            'preferred_contact__name': data.preferred_contact.name if data.preferred_contact else '',
            'preferred_contact__email': data.preferred_contact.email if data.preferred_contact else '',
            'preferred_contact__title': data.preferred_contact.title if data.preferred_contact else '',
            'cost_centre__division__manager__name': cost_centre__division__manager__name,
            'cost_centre__division__manager__email': cost_centre__division__manager__email,
            'cost_centre__division__manager__title': cost_centre__division__manager__title,
            'cost_centre__division__name': cost_centre__division__name,
            'cost_centre__name': cost_centre__name,
            'cost_centre__code': cost_centre__code,
            'owner__name': data.owner.name if data.owner else '',
            'owner__email': data.owner.email if data.owner else '',
            'owner__title': data.owner.title if data.owner else '',
            'custodian__name': data.custodian.name if data.custodian else '',
            'custodian__email': data.custodian.email if data.custodian else '',
            'custodian__title': data.custodian.title if data.custodian else '',
            'data_custodian__name': data.data_custodian.name if data.data_custodian else '',
            'data_custodian__email': data.data_custodian.email if data.data_custodian else '',
            'data_custodian__title': data.data_custodian.title if data.data_custodian else '',
            'link': data.link,
            'status_html': data.status_html or '',
            'schema': data.schema_url or '',
            'system_reqs': data.system_reqs,
            'system_type': data.system_type_display or '',
            'vulnerability_docs': data.vulnerability_docs,
            'workaround': data.workaround,
            'recovery_docs': data.recovery_docs,
            'bh_support': {'name': data.bh_support.name, 'email': data.bh_support.email, 'telephone': data.bh_support.telephone} if data.bh_support else {},
            'ah_support': {'name': data.ah_support.name, 'email': data.ah_support.email, 'telephone': data.ah_support.telephone} if data.ah_support else {},
            'availability': data.availability_display or '',
            'status_display': data.status_display or '',
            'criticality': data.criticality_display or '',
            'mtd': format_timedelta(data.mtd),
            'rto': format_timedelta(data.rto),
            'rpo': format_timedelta(data.rpo),
            'softwares': [{
                'name': i.name,
                'url': i.url,
                'license': i.license.name if i.license else '',
                'license__url': i.license.url if i.license else '',
                'support': i.license.support if i.license else '',
                'support__url': i.license.support_url if i.license else '',
            } for i in data.softwares.all()],
            'hardwares': [{
                'host': i.host.name,
                'role': i.get_role_display(),
                'host__location': i.host.location.name if i.host.location else '',
                'operating_system': i.host.os.name if i.host.os else '',
                'operating_system__url': i.host.os.url if i.host.os else '',
                'operating_system__license': i.host.os.license.name if (i.host.os and i.host.os.license) else '',
                'operating_system__license__url': i.host.os.license.url if (i.host.os and i.host.os.license) else '',
                'operating_system__support': i.host.os.license.support if (i.host.os and i.host.os.license) else '',
                'operating_system__support__url': i.host.os.license.support_url if (i.host.os and i.host.os.license) else '',
                'backup': i.host.backup.get_os_schedule_display() if (hasattr(i, 'host.backup') and i.host.backup) else '',
                'backup_test_date': i.host.backup.last_tested.isoformat() if (hasattr(i, 'host.backup') and i.host.backup and i.host.backup.last_tested) else '',

            } for i in data.hardwares.all()],
            'processes': {'relationships': [{
                'process__name': i.process.name,
                'process__criticality': i.process.get_criticality_display() if i.process.criticality else '',
                'process__importance': i.get_importance_display(),
                # Flatten the function(s) associated with the process.
                'function__name': ', '.join(f.name for f in i.process.functions.all()),
                # One nest listed comprehension to rule them all.
                'function__service': ', '.join(sorted(set(
                    [str(s.number) for s in list(
                        itertools.chain.from_iterable(
                            [f.services.all() for f in i.process.functions.all()]
                        )
                    )]
                )))
            } for i in data.processitsystemrelationship_set.all().order_by('importance')]},
            'dependencies': {'relationships': [{
                'dependency__system_id': i.dependency.system_id,
                'dependency__name': i.dependency.name,
                'criticality': i.get_criticality_display()
            } for i in data.itsystemdependency_set.all()]},
            'usergroups': [{'name': i.name, 'count': i.user_count} for i in data.user_groups.all()],
            'contingency_plan_url': domain + settings.MEDIA_URL + data.contingency_plan.name if data.contingency_plan else '',
            'contingency_plan_status': data.get_contingency_plan_status_display(),
            'contingency_plan_last_tested': data.contingency_plan_last_tested,
        }
        return prepped

    def list_qs(self):
        # Only return production apps
        FILTERS = {"status": 0}
        if "all" in self.request.GET:
            del FILTERS["status"]
        if "system_id" in self.request.GET:
            del FILTERS["status"]
            FILTERS["system_id__icontains"] = self.request.GET["system_id"]
        if "name" in self.request.GET:
            FILTERS["name"] = self.request.GET["name"]
        if "pk" in self.request.GET:
            FILTERS["pk"] = self.request.GET["pk"]
        return ITSystem.objects.filter(**FILTERS)

    def list(self):
        return list(self.list_qs())


class UserResource(DjangoResource):
    COMPACT_ARGS = (
        "pk", "name", "title", "employee_id", "email", "telephone", "mobile_phone", "photo", "photo_ad",
        "org_data", "parent__email", "parent__name", "username", "org_unit__location__id", "org_unit__location__name",
        "org_unit__location__address", "org_unit__location__pobox", "org_unit__location__phone",
        "org_unit__location__fax", "ad_guid", "notes", "working_hours", "org_unit__secondary_location__name"
    )
    VALUES_ARGS = COMPACT_ARGS + (
        "ad_dn", "ad_data", "date_updated", "date_ad_updated", "active", "ad_deleted",
        "in_sync", "given_name", "surname", "home_phone", "other_phone")

    PROPERTY_ARGS = (
        "password_age_days",
    )

    formatters = FieldsFormatter(formatters={
        "photo": format_fileField,
        "photo_ad": format_fileField
    })

    def is_authenticated(self):
        return True

    def org_structure(self):
        qs = DepartmentUser.objects.filter(**DepartmentUser.ACTIVE_FILTER)
        structure = []
        orgunits = OrgUnit.objects.all()
        costcentres = CostCentre.objects.all()
        locations = Location.objects.all()
        slocations = SecondaryLocation.objects.all()
        defaultowner = "support@dpaw.wa.gov.au"
        for obj in orgunits:
            structure.append({"id": 'db-org_{}'.format(obj.pk),
                              "name": str(obj), "email": slugify(obj.name), "owner": getattr(obj.manager, "email", defaultowner),
                              "members": [d[0] for d in qs.filter(org_unit__in=obj.get_descendants(include_self=True)).values_list("email")]})
        for obj in costcentres:
            structure.append({"id": 'db-cc_{}'.format(obj.pk),
                              "name": str(obj), "email": slugify(obj.name), "owner": getattr(obj.manager, "email", defaultowner),
                              "members": [d[0] for d in qs.filter(cost_centre=obj).values_list("email")]})
        for obj in locations:
            structure.append({"id": 'db-loc_{}'.format(obj.pk),
                              "name": str(obj), "email": slugify(obj.name) + "-location", "owner": getattr(obj.manager, "email", defaultowner),
                              "members": [d[0] for d in qs.filter(org_unit__location=obj).values_list("email")]})
        for obj in slocations:
            structure.append({"id": 'db-locs_{}'.format(obj.pk),
                              "name": str(obj), "email": slugify(obj.name) + "-location", "owner": getattr(obj.manager, "email", defaultowner),
                              "members": [d[0] for d in qs.filter(org_unit__secondary_location=obj).values_list("email")]})
        for row in structure:
            if row["members"]:
                row["email"] = "{}@{}".format(
                    row["email"], row["members"][0].split("@", 1)[1])
        return structure

    def list(self):
        FILTERS = DepartmentUser.ACTIVE_FILTER.copy()
        if "org_structure" in self.request.GET:
            return self.org_structure()
        if "all" in self.request.GET:
            FILTERS = {}
        if "cost_centre" in self.request.GET:
            FILTERS["cost_centre__code"] = self.request.GET["cost_centre"]
        if "email" in self.request.GET:
            FILTERS["email__iexact"] = self.request.GET["email"]
        if "ad_guid" in self.request.GET:
            FILTERS["ad_guid__endswith"] = self.request.GET["ad_guid"]
        if "compact" in self.request.GET:
            self.VALUES_ARGS = self.COMPACT_ARGS
        users = DepartmentUser.objects.filter(**FILTERS).order_by("name")
        user_values = list(users.values(*self.VALUES_ARGS))
        for i, user in enumerate(user_values):
            user.update({key: getattr(users[i], key) for key in self.PROPERTY_ARGS})
        
        return self.formatters.format(self.request, user_values)

    @skip_prepare
    def create(self):
        try:
            try:
                user = DepartmentUser.objects.get(
                    email__iexact=self.data["EmailAddress"])
            except:
                try:
                    user = DepartmentUser.objects.get(
                        ad_guid__iendswith=self.data["ObjectGUID"])
                except:
                    try:
                        user = DepartmentUser.objects.get(
                            ad_dn=self.data["DistinguishedName"])
                    except:
                        user = DepartmentUser(ad_guid=self.data["ObjectGUID"])
            if self.data.get("Deleted"):
                user.active = False
                user.ad_deleted = True
                user.ad_updated = True
                user.save()
                data = list(
                    DepartmentUser.objects.filter(
                        pk=user.pk).values(
                        *self.VALUES_ARGS))[0]
                return self.formatters.format(self.request, data)
            modified = make_aware(
                user._meta.get_field_by_name("date_updated")[0].clean(
                    self.data["Modified"], user))
            if not user.pk or not user.date_ad_updated or modified > user.date_updated:
                user.email = self.data["EmailAddress"]
                user.ad_guid = self.data["ObjectGUID"]
                user.ad_dn = self.data["DistinguishedName"]
                user.username = self.data["SamAccountName"]
                user.expiry_date = self.data.get("AccountExpirationDate")
                user.active = self.data["Enabled"]
                user.ad_deleted = False
                user.ad_data = self.data
                if not user.name:
                    user.name = self.data["Name"]
                if not user.title:
                    user.title = self.data["Title"]
                if not user.given_name:
                    user.given_name = self.data["GivenName"]
                if not user.surname:
                    user.surname = self.data["Surname"]
                user.date_ad_updated = self.data["Modified"]
                user.ad_updated = True
                user.save()
            data = list(
                DepartmentUser.objects.filter(
                    pk=user.pk).values(
                    *self.VALUES_ARGS))[0]
        except Exception as e:
            data = self.data
            data["Error"] = repr(e)
        return self.formatters.format(self.request, data)


@csrf_exempt
def profile(request):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    # Profile API view should return one object only.
    self = UserResource()
    if not hasattr(request, 'user') or not request.user.email:
        return HttpResponseBadRequest('No user email in request')
    qs = DepartmentUser.objects.filter(email__iexact=request.user.email)
    if qs.count() > 1 or qs.count() < 1:
        return HttpResponseBadRequest('API request for {} should return one profile; it returned {}!'.format(
            request.user.email, qs.count()))
    user = qs.get(email__iexact=request.user.email)

    if request.method == "GET":
        data = qs.values(*self.VALUES_ARGS)[0]
        # Add the password_age_days property to the API response.
        data['password_age_days'] = user.password_age_days
    elif request.method == "POST":
        if 'photo' in request.POST and request.POST['photo'] == 'delete':
            user.photo.delete()
        elif 'photo' in request.FILES:
            user.photo.save(
                request.FILES['photo'].name,
                request.FILES['photo'],
                save=False)
        if 'telephone' in request.POST:
            user.telephone = request.POST['telephone']
        if 'mobile_phone' in request.POST:
            user.mobile_phone = request.POST['mobile_phone']
        if 'other_phone' in request.POST:
            user.other_phone = request.POST['other_phone']
        if 'preferred_name' in request.POST:
            user.preferred_name = request.POST['preferred_name']
        user.save()
        data = DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS)[0]
    return HttpResponse(json.dumps(
        {'objects': [self.formatters.format(request, data)]}, cls=MoreTypesJSONEncoder))
