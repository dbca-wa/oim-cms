from registers.models import CostCentre, ITSystem, Hardware, OrgUnit, Location, SecondaryLocation
from core.models import UserSession
from tracking.models import DepartmentUser
from django.utils.text import slugify
from django.utils.timezone import make_aware

import json
import requests
from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer
from restless.resources import skip_prepare
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.db.models import Count

from django.views.decorators.csrf import csrf_exempt
from djqscsv import render_to_csv_response


class CSVDjangoResource(DjangoResource):
    @classmethod
    def as_csv(cls, request):
        resource = cls()
        if not hasattr(resource, "list_qs"):
            return HttpResponse("list_qs not implemented for {}".format(cls.__name__))
        resource.request = request
        return render_to_csv_response(resource.list_qs(), field_order=resource.VALUES_ARGS)


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
                      auth=settings.FRESHDESK_AUTH, headers={"Content-Type": "application/json"},
                      data=json.dumps(ticket))
    ticket_id = json.loads(r.content)["helpdesk_ticket"]["display_id"]
    return HttpResponseRedirect(settings.FRESHDESK_ENDPOINT + "/support/tickets/{}".format(ticket_id))


class OptionResource(DjangoResource):
    @skip_prepare
    def list(self):
        return getattr(self, "data_" + self.request.GET["list"])()

    def data_cost_centre(self):
        return ["{} {}".format(*c) for c in CostCentre.objects.filter(active=True).values_list("code", "name")]

    def data_dept_user(self):
        return [u[0] for u in DepartmentUser.objects.filter(active=True, email__iendswith=".wa.gov.au").order_by("email").values_list("email")]

    def data_itsystem(self):
        return ["{} {}".format(*s) for s in ITSystem.objects.all().values_list("system_id", "name")]


class whoamiResource(DjangoResource):
    preparer = FieldsPreparer(fields={
        'email': 'user.email',
        'username': 'user.username',
        'first_name': 'user.first_name',
        'last_name': 'user.last_name',
        'shared_id': 'shared_id',
        'session_key': 'session.session_key',
        'client_logon_ip': 'ip'
    })

    def detail(self):
        return UserSession.objects.get(session__session_key=self.request.session.session_key)


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
            FILTERS["computer__hostname__istartswith"] = self.request.GET["hostname"]
        if self.request.GET.get("local_current", "").lower() == "false":
            FILTERS["local_current"] = False
        data = list(Hardware.objects.filter(**FILTERS).values(*self.VALUES_ARGS))
        for row in data:
            row.update(json.loads(row["local_info"]))
        return data

    @skip_prepare
    def create(self):
        computer = Hardware.objects.get(computer__hostname__istartswith=self.data["hostname"])
        local_info = json.dumps(self.data)
        computer.local_info = local_info
        computer.local_current = self.data.get("local_current", False)
        computer.save()
        data = list(Hardware.objects.filter(pk=computer.pk).values(*self.VALUES_ARGS))[0]
        data.update(json.loads(data["local_info"]))
        return data


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
    VALUES_ARGS = (
        "pk", "name", "acronym", "system_id",
        "link", "cost_centre__code",
        "cost_centre__name",
        "cost_centre__division__name",
        "cost_centre__division__manager__name",
        "owner__name", "owner__email",
        "custodian__name", "custodian__email",
        "data_custodian__name", "data_custodian__email",
        "preferred_contact__name", "preferred_contact__email",
        "documentation", "access_display",
        "authentication_display", "status_html", "status_display",
        "description")

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
        return ITSystem.objects.filter(**FILTERS).values(*self.VALUES_ARGS)

    @skip_prepare
    def list(self):
        return list(self.list_qs())


class UserResource(DjangoResource):
    COMPACT_ARGS = (
        "pk", "name", "title", "employee_id", "email", "telephone", "mobile_phone",
        "org_data", "parent__email", "parent__name", "username", "org_unit__location__id", "org_unit__location__name",
        "org_unit__location__address", "org_unit__location__pobox", "org_unit__location__phone",
        "org_unit__location__fax", "ad_guid"
    )
    VALUES_ARGS = COMPACT_ARGS + (
        "ad_dn", "ad_data", "date_updated", "date_ad_updated", "active", "ad_deleted",
        "in_sync", "given_name", "surname", "home_phone", "other_phone")

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
                row["email"] = "{}@{}".format(row["email"], row["members"][0].split("@", 1)[1])
        return structure

    @skip_prepare
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
        return list(DepartmentUser.objects.filter(**FILTERS).order_by("name").values(*self.VALUES_ARGS))

    @skip_prepare
    def create(self):
        try:
            try:
                user = DepartmentUser.objects.get(email__iexact=self.data["EmailAddress"])
            except:
                try:
                    user = DepartmentUser.objects.get(ad_guid__iendswith=self.data["ObjectGUID"])
                except:
                    try:
                        user = DepartmentUser.objects.get(ad_dn=self.data["DistinguishedName"])
                    except:
                        user = DepartmentUser(ad_guid=self.data["ObjectGUID"])
            if self.data.get("Deleted"):
                user.active = False
                user.ad_deleted = True
                user.ad_updated = True
                user.save()
                data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
                return data
            modified = make_aware(user._meta.get_field_by_name("date_updated")[0].clean(self.data["Modified"], user))
            if not user.pk or not user.date_ad_updated or modified > user.date_updated:
                user.email = self.data["EmailAddress"]
                user.ad_guid = self.data["ObjectGUID"]
                user.ad_dn = self.data["DistinguishedName"]
                user.username = self.data["SamAccountName"]
                user.expiry_date = self.data.get("AccountExpirationDate")
                user.active = self.data["Enabled"]
                user.ad_data = self.data
                if not user.name: user.name = self.data["Name"]
                if not user.title: user.title = self.data["Title"]
                if not user.given_name: user.given_name = self.data["GivenName"]
                if not user.surname: user.surname = self.data["Surname"]
                user.date_ad_updated = self.data["Modified"]
                user.ad_updated = True
                print("{}{}".format(user, user.date_updated))
                user.save()
            data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
        except Exception as e:
            data = self.data
            data["Error"] = repr(e)
        return data
