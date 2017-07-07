from __future__ import unicode_literals, absolute_import
from django.conf import settings
from django.conf.urls import url
from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseBadRequest)
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
import json
from restless.constants import OK
from restless.dj import DjangoResource
from restless.exceptions import BadRequest
from restless.resources import skip_prepare
from restless.utils import MoreTypesJSONEncoder
from oim_cms.utils import FieldsFormatter, CSVDjangoResource
import logging

from .models import DepartmentUser, Location, SecondaryLocation, OrgUnit, CostCentre


ACCOUNT_TYPE_DICT = dict(DepartmentUser.ACCOUNT_TYPE_CHOICES)
logger = logging.getLogger('ad_sync')


def format_fileField(request, value):
    if value:
        return request.build_absolute_uri(
            '{}{}'.format(settings.MEDIA_URL, value))
    else:
        return value


def format_position_type(request, value):
    position_type = dict(DepartmentUser.POSITION_TYPE_CHOICES)
    if value is not None:
        return position_type[value]
    else:
        return value


def format_account_type(request, value):
    if value is not None:
        return ACCOUNT_TYPE_DICT[value]
    else:
        return value


class DepartmentUserResource(DjangoResource):
    """An API Resource class to represent DepartmentUser objects.
    This class is used to create & update synchronised user account data from
    Active Directory.
    It also includes custom endpoints to return the P&W organisation
    structure membership.
    """
    COMPACT_ARGS = (
        'pk', 'name', 'title', 'employee_id', 'email', 'telephone',
        'mobile_phone', 'extension', 'photo', 'photo_ad', 'org_data', 'parent__email',
        'parent__name', 'username', 'org_unit__location__id',
        'org_unit__location__name', 'org_unit__location__address',
        'org_unit__location__pobox', 'org_unit__location__phone',
        'org_unit__location__fax', 'ad_guid',
        'org_unit__secondary_location__name', 'preferred_name',
        'expiry_date')
    VALUES_ARGS = COMPACT_ARGS + (
        'ad_dn', 'ad_data', 'date_updated', 'date_ad_updated', 'active',
        'ad_deleted', 'in_sync', 'given_name', 'surname', 'home_phone',
        'other_phone', 'notes', 'working_hours', 'position_type',
        'account_type', 'o365_licence', 'shared_account')
    MINIMAL_ARGS = (
        'pk', 'name', 'preferred_name', 'title', 'email', 'telephone',
        'mobile_phone', 'photo', 'org_unit__location__name')
    PROPERTY_ARGS = ('password_age_days',)

    formatters = FieldsFormatter(formatters={
        'photo': format_fileField,
        'photo_ad': format_fileField,
        'position_type': format_position_type,
        'account_type': format_account_type,
    })

    def prepare(self, data):
        """Modify the returned object to append the GAL Department value.
        """
        prepped = super(DepartmentUserResource, self).prepare(data)
        if 'pk' in data:
            prepped['gal_department'] = DepartmentUser.objects.get(pk=data['pk']).get_gal_department()
        if 'expiry_date' in data:
            if data['expiry_date'] and data['expiry_date'] < timezone.now():
                data['ad_expired'] = True
            else:
                data['ad_expired'] = False
        return prepped

    @classmethod
    def urls(self, name_prefix=None):
        """Override the DjangoResource ``urls`` class method so the detail view
        accepts a GUID parameter instead of PK.
        """
        return [
            url(r'^$', self.as_list(), name=self.build_url_name('list', name_prefix)),
            url(r'^(?P<guid>[0-9A-Za-z-@\'&\.]+)/$', self.as_detail(), name=self.build_url_name('detail', name_prefix)),
        ]

    def build_response(self, data, status=OK):
        resp = super(DepartmentUserResource, self).build_response(data, status)
        # Require a short caching expiry for certain request types (if defined).
        if settings.API_RESPONSE_CACHE_SECONDS:
            if any(k in self.request.GET for k in ['email', 'compact', 'minimal']):
                resp['Cache-Control'] = 'max-age={}, public'.format(settings.API_RESPONSE_CACHE_SECONDS)
        return resp

    def is_authenticated(self):
        """This method is currently required for create/update to work via the
        AD sync scripts.
        TODO: implement optional token-based auth to secure this.
        """
        return True

    def list(self):
        """Pass query params to modify the API output.
        Include `org_structure=true` and `sync_o365=true` to output only
        OrgUnits with sync_o365 == True.
        Include `populate_groups=true` to output only DepartmentUsers
        with populate_primary_group == True.
        """
        FILTERS = {}
        sync_o365 = True
        if 'sync_o365' in self.request.GET and self.request.GET['sync_o365'] == 'false':
            sync_o365 = False
        else:
            sync_o365 = True
        if 'populate_groups' in self.request.GET and self.request.GET['populate_groups'] == 'true':
            exclude_populate_groups = True  # Will exclude populate_primary_group == False
        else:
            exclude_populate_groups = False  # Will ignore populate_primary_group
        # org_structure response.
        if 'org_structure' in self.request.GET:
            return self.org_structure(sync_o365=sync_o365, exclude_populate_groups=exclude_populate_groups)
        # DepartmentUser object response.
        # Some of the request parameters below are mutually exclusive.
        if 'all' in self.request.GET:
            # Return all objects, including those deleted in AD.
            users = DepartmentUser.objects.all()
        elif 'ad_deleted' in self.request.GET:
            if self.request.GET['ad_deleted'] == 'false':
                # Return all objects that are not deleted in AD.
                users = DepartmentUser.objects.filter(ad_deleted=False)
            elif self.request.GET['ad_deleted'] == 'true':
                # Return all objects that are deleted in AD.
                users = DepartmentUser.objects.filter(ad_deleted=True)
        elif 'email' in self.request.GET:
            # Always return an object by email.
            users = DepartmentUser.objects.filter(email__iexact=self.request.GET['email'])
        elif 'ad_guid' in self.request.GET:
            # Always return an object by UUID.
            users = DepartmentUser.objects.filter(ad_guid=self.request.GET['ad_guid'])
        elif 'cost_centre' in self.request.GET:
            # Always return all objects by cost centre (inc inactive & contractors).
            users = DepartmentUser.objects.filter(cost_centre__code=self.request.GET['cost_centre'])
        else:
            # No other filtering:
            # Return 'active' DU objects, excluding predefined account types and contractors.
            FILTERS = DepartmentUser.ACTIVE_FILTER.copy()
            users = DepartmentUser.objects.filter(**FILTERS).exclude(account_type__in=[4, 5, 9, 10, 11, 12, 14, 15, 16])
            users = users.exclude(expiry_date__lte=timezone.now())
        # Non-mutually-exclusive filters:
        if 'o365_licence' in self.request.GET:
            if self.request.GET['o365_licence'].lower() == 'true':
                users = users.filter(o365_licence=True)
            elif self.request.GET['o365_licence'].lower() == 'false':
                users = users.filter(o365_licence=False)

        users = users.order_by('name')
        # Parameters to modify the API output.
        if 'compact' in self.request.GET:
            self.VALUES_ARGS = self.COMPACT_ARGS
        elif 'minimal' in self.request.GET:
            self.VALUES_ARGS = self.MINIMAL_ARGS

        user_values = list(users.values(*self.VALUES_ARGS))
        return self.formatters.format(self.request, user_values)

    def detail(self, guid):
        """Detail view for a single DepartmentUser object.
        """
        user = DepartmentUser.objects.filter(ad_guid=guid)
        if not user:
            user = DepartmentUser.objects.filter(email__iexact=guid.lower())
        user_values = list(user.values(*self.VALUES_ARGS))
        return self.formatters.format(self.request, user_values)[0]

    @skip_prepare
    def create(self):
        """Create view for a new DepartmentUserObject.
        BUSINESS RULE: we call this endpoint from AD, and require a
        complete request body that includes a GUID.
        """
        if 'ObjectGUID' not in self.data:
            raise BadRequest('Missing ObjectGUID parameter')
        try:
            user = DepartmentUser.objects.get_or_create(
                ad_guid=self.data['ObjectGUID'],
                email=self.data['EmailAddress'].lower(),
                ad_dn=self.data['DistinguishedName'],
                username=self.data['SamAccountName'],
                expiry_date=self.data['AccountExpirationDate'],
                active=self.data['Enabled'],
                name=self.data['DisplayName'],
                title=self.data['Title'],
                given_name=self.data['GivenName'],
                surname=self.data['Surname'],
                date_ad_updated=self.data['Modified'],
            )[0]
        except Exception as e:
            data = self.data
            data['Error'] = repr(e)
            logger.error(repr(e))
            return self.formatters.format(self.request, {'Error': repr(e)})

        # Serialise the newly-created DepartmentUser.
        data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
        logger.info('Created user {}'.format(user.email))
        logger.info('{} '.format(self.formatters.format(self.request, data)))

        return self.formatters.format(self.request, data)

    def update(self, guid):
        """Update view to handle changes to a DepartmentUser object.
        This view also handles marking users as 'Inactive' or 'Deleted'
        within AD.
        """
        try:
            user = DepartmentUser.objects.get(ad_guid=guid)
        except DepartmentUser.DoesNotExist:
            try:
                user = DepartmentUser.objects.get(email__iexact=guid.lower())
            except DepartmentUser.DoesNotExist:
                raise BadRequest('Object not found')

        try:
            if 'ObjectGUID' in self.data and self.data['ObjectGUID']:
                user.ad_guid = self.data['ObjectGUID']
            if 'EmailAddress' in self.data and self.data['EmailAddress']:
                user.email = self.data['EmailAddress'].lower()
            if 'DistinguishedName' in self.data and self.data['DistinguishedName']:
                user.ad_dn = self.data['DistinguishedName']
            if 'SamAccountName' in self.data and self.data['SamAccountName']:
                user.username = self.data['SamAccountName']
            if 'AccountExpirationDate' in self.data and self.data['AccountExpirationDate']:
                user.expiry_date = self.data['AccountExpirationDate']
            if 'Enabled' in self.data:  # Boolean; don't only work on True!
                user.active = self.data['Enabled']
            if 'DisplayName' in self.data and self.data['DisplayName']:
                user.name = self.data['DisplayName']
            if 'Title' in self.data and self.data['Title']:
                user.title = self.data['Title']
            if 'GivenName' in self.data and self.data['GivenName']:
                user.given_name = self.data['GivenName']
            if 'Surname' in self.data and self.data['Surname']:
                user.surname = self.data['Surname']
            if 'Modified' in self.data and self.data['Modified']:
                user.date_ad_updated = self.data['Modified']
            if 'o365_licence' in self.data:  # Boolean; don't only work on True!
                user.o365_licence = self.data['o365_licence']
            if 'Deleted' in self.data and self.data['Deleted']:
                user.active = False
                user.ad_deleted = True
                user.ad_guid = ''
                data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
                logger.info('Set user {} as deleted in AD'.format(user.name))
            else:
                user.ad_deleted = False
            user.ad_data = self.data  # Store the raw request data.
            user.ad_updated = True
            user.save()
        except Exception as e:
            data = self.data
            data['Error'] = repr(e)
            logger.error(repr(e))
            return self.formatters.format(self.request, {'Error': repr(e)})

        data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
        logger.info('Updated user {}'.format(user.email))
        logger.info('{}'.format(self.formatters.format(self.request, data)))

        return self.formatters.format(self.request, data)

    def org_structure(self, sync_o365=False, exclude_populate_groups=False):
        """A custom API endpoint to return the organisation structure: a list
        of each organisational unit's metadata (name, manager, members).
        Includes OrgUnits, cost centres, locations and secondary locations.
        """
        qs = DepartmentUser.objects.filter(**DepartmentUser.ACTIVE_FILTER)
        # Exclude predefined account types:
        qs = qs.exclude(account_type__in=[4, 5, 9, 10, 11, 12, 14, 15, 16])
        if exclude_populate_groups:  # Exclude objects where populate_primary_group == False
            qs = qs.exclude(populate_primary_group=False)
        structure = []
        if sync_o365:  # Exclude certain things from populating O365/AD
            orgunits = OrgUnit.objects.filter(unit_type__in=[0, 1], sync_o365=True)
            costcentres = []
            locations = Location.objects.filter(active=True)
            slocations = []
        else:
            orgunits = OrgUnit.objects.filter(active=True)
            costcentres = CostCentre.objects.filter(active=True)
            locations = Location.objects.filter(active=True)
            slocations = SecondaryLocation.objects.all()
        defaultowner = 'support@dpaw.wa.gov.au'
        for obj in orgunits:
            members = [d[0] for d in qs.filter(org_unit__in=obj.get_descendants(include_self=True)).values_list('email')]
            # We also need to iterate through DepartmentUsers to add those with
            # secondary OrgUnits to each OrgUnit.
            for i in DepartmentUser.objects.filter(org_units_secondary__isnull=False):
                if obj in i.org_units_secondary.all():
                    members.append(i.email)
            structure.append({'id': 'db-org_{}'.format(obj.pk),
                              'name': str(obj),
                              'email': slugify(obj.name),
                              'owner': getattr(obj.manager, 'email', defaultowner),
                              'members': list(set(members))})
        for obj in costcentres:
            members = [d[0] for d in qs.filter(cost_centre=obj).values_list('email')]
            # We also need to iterate through DepartmentUsers to add those with
            # secondary CCs as members to each CostCentre.
            for i in DepartmentUser.objects.filter(cost_centres_secondary__isnull=False):
                if obj in i.cost_centres_secondary.all():
                    members.append(i.email)
            structure.append({'id': 'db-cc_{}'.format(obj.pk),
                              'name': str(obj),
                              'email': slugify(obj.name),
                              'owner': getattr(obj.manager, 'email', defaultowner),
                              'members': list(set(members))})
        for obj in locations:
            members = [d[0] for d in qs.filter(org_unit__location=obj).values_list('email')]
            # We also need to iterate through DepartmentUsers to add those with
            # secondary locations as members to each Location.
            for i in DepartmentUser.objects.filter(secondary_locations__isnull=False):
                if obj in i.secondary_locations.all():
                    members.append(i.email)
            structure.append({'id': 'db-loc_{}'.format(obj.pk),
                              'name': str(obj),
                              'email': slugify(obj.name) + '-location',
                              'owner': getattr(obj.manager, 'email', defaultowner),
                              'members': members})
        for obj in slocations:
            structure.append({'id': 'db-locs_{}'.format(obj.pk),
                              'name': str(obj),
                              'email': slugify(obj.name) + '-location',
                              'owner': getattr(obj.manager, 'email', defaultowner),
                              'members': [d[0] for d in qs.filter(org_unit__secondary_location=obj).values_list('email')]})
        for row in structure:
            if row['members']:
                row['email'] = '{}@{}'.format(
                    row['email'], row['members'][0].split('@', 1)[1])
        return structure


class LocationResource(CSVDjangoResource):
    VALUES_ARGS = (
        'pk', 'name', 'address', 'phone', 'fax', 'email', 'point', 'url', 'bandwidth_url', 'active')

    def list_qs(self):
        FILTERS = {}
        if 'location_id' in self.request.GET:
            FILTERS['pk'] = self.request.GET['location_id']
        else:
            FILTERS['active'] = True
        return Location.objects.filter(**FILTERS).values(*self.VALUES_ARGS)

    @skip_prepare
    def list(self):
        data = list(self.list_qs())
        for row in data:
            if row['point']:
                row['point'] = row['point'].wkt
        return data


@csrf_exempt
def profile(request):
    """An API view that returns the profile for the request user.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden()

    # Profile API view should return one object only.
    self = DepartmentUserResource()
    if not hasattr(request, 'user') or not request.user.email:
        return HttpResponseBadRequest('No user email in request')
    qs = DepartmentUser.objects.filter(email__iexact=request.user.email)
    if qs.count() > 1 or qs.count() < 1:
        return HttpResponseBadRequest('API request for {} should return one profile; it returned {}!'.format(
            request.user.email, qs.count()))
    user = qs.get(email__iexact=request.user.email)

    if request.method == 'GET':
        data = qs.values(*self.VALUES_ARGS)[0]
        # Add the password_age_days property to the API response.
        data['password_age_days'] = user.password_age_days
    elif request.method == 'POST':
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
        if 'extension' in request.POST:
            user.extension = request.POST['extension']
        if 'other_phone' in request.POST:
            user.other_phone = request.POST['other_phone']
        if 'preferred_name' in request.POST:
            user.preferred_name = request.POST['preferred_name']
        user.save()
        data = DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS)[0]
    return HttpResponse(json.dumps(
        {'objects': [self.formatters.format(request, data)]}, cls=MoreTypesJSONEncoder),
        content_type='application/json')
