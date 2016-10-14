from __future__ import unicode_literals, absolute_import
from django.conf import settings
from django.conf.urls import include, url
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
import json
from mptt.templatetags.mptt_tags import cache_tree_children
import requests
from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer
from restless.resources import skip_prepare

from approvals.api import ApprovalResource
from core.models import UserSession
from mudmap.models import MudMap
from organisation.api import DepartmentUserResource, LocationResource, profile
from organisation.models import DepartmentUser, Location, OrgUnit, CostCentre
from registers.api import ITSystemResource, HardwareResource
from registers.models import ITSystem
from tracking.api import EC2InstanceResource

from .utils import CSVDjangoResource


@csrf_exempt
def freshdesk(request):
    """An API view to create a new Freshdesk ticket via a POST to the
    Freshdesk API.
    """
    lines = []
    for key, val in request.POST.iteritems():
        if not val:
            val = '(blank)'
        lines.append('<li><b>{}</b>: {}</li>'.format(key, val))
    lines.sort()
    description = '<ul>{}</ul>'.format(''.join(lines))
    ticket = {'helpdesk_ticket': {
        'subject': request.POST.get('subject', 'Form submitted'),
        'email': request.user.email,
        'priority': int(request.POST.get('priority', 1)),
        'status': int(request.POST.get('status', 2)),
        'description_html': description,
        'source': 4
    }}
    r = requests.post(settings.FRESHDESK_ENDPOINT + '/helpdesk/tickets.json',
                      auth=settings.FRESHDESK_AUTH, headers={
                          'Content-Type': 'application/json'},
                      data=json.dumps(ticket))
    ticket_id = json.loads(r.content)['helpdesk_ticket']['display_id']
    return HttpResponseRedirect(
        settings.FRESHDESK_ENDPOINT + '/support/tickets/{}'.format(ticket_id))


def recursive_node_to_dict(node):
    # http://stackoverflow.com/questions/12556268/fastest-way-to-create-json-to-reflect-a-tree-structure-in-python-django-using
    result = {
        'name': node.name, 'id': node.pk,
        'children': [recursive_node_to_dict(c) for c in node._cached_children]
    }
    if not result['children']:
        del result['children']
    return result


class OptionResource(DjangoResource):
    """Returns serialised lists of object data. Request parameter must include
    ``list`` value of a defined function (below), minus the ``data_`` prefix.
    Example:
    /api/options?list=org_structure
    """

    @skip_prepare
    def list(self):
        return getattr(self, 'data_' + self.request.GET['list'])()

    def data_org_structure(self):
        return [recursive_node_to_dict(cache_tree_children(dept.get_descendants_active(include_self=True))[0])
                for dept in OrgUnit.objects.filter(unit_type=0).order_by('name')]

    def data_cost_centre(self):
        return ['CC{} / {}'.format(*c) for c in CostCentre.objects.all().exclude(org_position__name__icontains='inactive').values_list('code', 'org_position__name')]

    def data_org_unit(self):
        return [{'name': i.name, 'id': i.pk} for i in OrgUnit.objects.all()]

    def data_dept_user(self):
        return [u[0] for u in DepartmentUser.objects.filter(
            active=True, email__iendswith='.wa.gov.au').order_by('email').values_list('email')]

    def data_itsystem(self):
        return ['{} {}'.format(
            *s) for s in ITSystem.objects.all().values_list('system_id', 'name')]

    def data_statuslogin(self):
        return [l[1] for l in list(ITSystem.STATUS_CHOICES) + list(ITSystem.ACCESS_CHOICES) + list(ITSystem.AUTHENTICATION_CHOICES)]

    def data_location(self):
        return [l.name for l in Location.objects.all().order_by('name')]

    def data_division(self):
        return [i.name for i in OrgUnit.objects.filter(unit_type=1).order_by('name')]

    def data_dept(self):
        return [i.acronym for i in OrgUnit.objects.filter(unit_type=0, acronym__gt='').order_by('name')]

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


class MudMapResource(CSVDjangoResource):
    VALUES_ARGS = (
        'pk', 'name', 'user', 'last_saved'
    )

    def is_authenticated(self):
        return True
        return self.data.get('name', '').startswith(
            self.request.user.email.lower())

    def list_qs(self):
        FILTERS = {}
        if 'mudmap_id' in self.request.GET:
            FILTERS['pk'] = self.request.GET['mudmap_id']
        return MudMap.objects.filter(**FILTERS).values(*self.VALUES_ARGS)

    @skip_prepare
    def list(self):
        data = list(self.list_qs())
        return data

    @skip_prepare
    def create(self):
        mudmap, created = MudMap.objects.get_or_create(name=self.data['name'])
        if 'delete' in self.data:
            mudmap.delete()
            return {'deleted': self.data['name']}
        else:
            mudmap.geojson = self.data['features']
            mudmap.lastsave = self.data['lastsave']
            mudmap.user = self.request.user
            mudmap.save()
            return {'saved': self.data['name']}


api_urlpatterns = [
    url(r'^approvals/', include(ApprovalResource.urls())),
    url(r'^freshdesk', freshdesk, name='api_freshdesk'),
    url(r'^ec2_instances/', include(EC2InstanceResource.urls())),
    url(r'^itsystems/', include(ITSystemResource.urls())),
    url(r'^itsystems.csv', ITSystemResource.as_csv),
    url(r'^mudmaps', include(MudMapResource.urls())),
    url(r'^mudmaps.csv', MudMapResource.as_csv),
    url(r'^locations/', include(LocationResource.urls())),
    url(r'^locations.csv', LocationResource.as_csv),
    url(r'^devices/', include(HardwareResource.urls())),
    url(r'^users/', include(DepartmentUserResource.urls())),
    url(r'^profile/', profile, name='api_profile'),
    url(r'^options', include(OptionResource.urls())),
    url(r'^whoami', WhoAmIResource.as_detail(), name='api_whoami'),
]
