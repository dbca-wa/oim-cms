from __future__ import unicode_literals, absolute_import
from django.conf import settings
from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseBadRequest)
from django.utils.text import slugify
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
import json
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
    COMPACT_ARGS = (
        'pk', 'name', 'title', 'employee_id', 'email', 'telephone',
        'mobile_phone', 'extension', 'photo', 'photo_ad', 'org_data', 'parent__email',
        'parent__name', 'username', 'org_unit__location__id',
        'org_unit__location__name', 'org_unit__location__address',
        'org_unit__location__pobox', 'org_unit__location__phone',
        'org_unit__location__fax', 'ad_guid',
        'org_unit__secondary_location__name', 'preferred_name')
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

    def org_structure(self, sync_o365=False, exclude_populate_groups=False):
        """A custom API endpoint to return the organisation structure: a list
        of each organisational unit's metadata (name, manager, members).
        Includes OrgUnits, cost centres, locations and secondary locations.
        """
        qs = DepartmentUser.objects.filter(**DepartmentUser.ACTIVE_FILTER)
        if exclude_populate_groups:  # Exclude objects where populate_primary_group == False
            qs = qs.exclude(populate_primary_group=False)
        structure = []
        if sync_o365:
            orgunits = OrgUnit.objects.filter(sync_o365=True)
        else:
            orgunits = OrgUnit.objects.all()
        costcentres = CostCentre.objects.all()
        locations = Location.objects.all()
        slocations = SecondaryLocation.objects.all()
        defaultowner = 'support@dpaw.wa.gov.au'
        for obj in orgunits:
            structure.append({'id': 'db-org_{}'.format(obj.pk),
                              'name': str(obj),
                              'email': slugify(obj.name),
                              'owner': getattr(obj.manager, 'email', defaultowner),
                              'members': [d[0] for d in qs.filter(org_unit__in=obj.get_descendants(include_self=True)).values_list('email')]})
        for obj in costcentres:
            structure.append({'id': 'db-cc_{}'.format(obj.pk),
                              'name': str(obj),
                              'email': slugify(obj.name),
                              'owner': getattr(obj.manager, 'email', defaultowner),
                              'members': [d[0] for d in qs.filter(cost_centre=obj).values_list('email')]})
        for obj in locations:
            structure.append({'id': 'db-loc_{}'.format(obj.pk),
                              'name': str(obj),
                              'email': slugify(obj.name) + '-location',
                              'owner': getattr(obj.manager, 'email', defaultowner),
                              'members': [d[0] for d in qs.filter(org_unit__location=obj).values_list('email')]})
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
            # Return 'active' DU objects, excluding shared/role-based accounts
            # and contractors.
            FILTERS = DepartmentUser.ACTIVE_FILTER.copy()
            users = DepartmentUser.objects.filter(**FILTERS).exclude(account_type__in=[5, 9])

        users = users.order_by('name')
        # Parameters to modify the API output.
        if 'compact' in self.request.GET:
            self.VALUES_ARGS = self.COMPACT_ARGS
        elif 'minimal' in self.request.GET:
            self.VALUES_ARGS = self.MINIMAL_ARGS

        user_values = list(users.values(*self.VALUES_ARGS))
        return self.formatters.format(self.request, user_values)

    def is_authenticated(self):
        """This method os currently required for create/update to work via the
        AD sync scripts.
        TODO: implement optional token-based auth to secure this).
        """
        return True

    @csrf_exempt
    def update(self, pk):
        """TODO: consolidate/refactor this method to remove duplication with
        the create method.
        """
        user = self.get_user()
        if user:
            if self.data.get('Deleted'):
                user.active = False
                user.ad_deleted = True
                user.ad_updated = True
                user.save()
                data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
                logger.info("Set user {} as deleted in AD\n{}".format(user.name,self.formatters.format(self.request, data)))
                return self.formatters.format(self.request, data)
            modified = make_aware(user._meta.get_field_by_name('date_updated')[0].clean(self.data['Modified'], user))
            if user.date_ad_updated or modified < user.date_updated:
                old_user = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
                updated_user_data = self.updateUser(user)
                data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
                log_data = {
                    'old_user': old_user['ad_data'],
                    'updated_user_data': updated_user_data.ad_data
                }
                logger.info("Updated user {}\n{}".format(user.name, self.formatters.format(self.request, log_data)))

            return self.formatters.format(self.request, data)
        else:
            logger.error("User does not exist")
            logger.info(self.data)
            return self.formatters.format(self.request, {"Error": "User does not exist"})

    @skip_prepare
    def create(self):
        """BUSINESS RULE: we allow POST requests for both create and update
        operations, because we will typically be calling this endpoint from
        systems where the DepartmentUser PK is unknown (we match existing
        objects by GUID or email).
        """
        user = self.get_user()
        if not user:
            if not self.data.get('ObjectGUID'):
                raise BadRequest('Missing ObjectGUID parameter')
            try:
                # For creation, we require the AD GUID.
                user = DepartmentUser(ad_guid=self.data['ObjectGUID'])
                user = self.updateUser(user)
                data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
                logger.info("Created User {} \n{} ".format(user.name, self.formatters.format(self.request, data)))
                return self.formatters.format(self.request, data)
            except Exception as e:
                data = self.data
                data['Error'] = repr(e)
                logger.error(repr(e))
                return self.formatters.format(self.request, {"Error": repr(e)})
        else:
            old_user_data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
            updated_user_data = self.updateUser(user)
            data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
            log_data = {
                'old_user_data': old_user_data['ad_data'],
                'updated_user_data': updated_user_data.ad_data
            }
            logger.info("Updated user {}\n{}".format(user.name, self.formatters.format(self.request, log_data)))
            return self.formatters.format(self.request, data)

    def updateUser(self, user):
        """Method to update a DepartmentUser object from AD data.
        The request parameters below reference the field name for AD objects.
        """
        try:
            if self.data.get('ObjectGUID'):
                user.ad_guid = self.data['ObjectGUID']
            if self.data.get('EmailAddress'):
                user.email = self.data['EmailAddress']
            if self.data.get('DistinguishedName'):
                user.ad_dn = self.data['DistinguishedName']
            if self.data.get('SamAccountName'):
                user.username = self.data['SamAccountName']
            if self.data.get('AccountExpirationDate'):
                user.expiry_date = self.data['AccountExpirationDate']
            if self.data.get('Enabled'):
                user.active = self.data['Enabled']
            if self.data.get('Name'):
                user.name = self.data['Name']
            if self.data.get('Title'):
                user.title = self.data['Title']
            if self.data.get('GivenName'):
                user.given_name = self.data['GivenName']
            if self.data.get('Surname'):
                user.surname = self.data['Surname']
            if self.data.get('Modified'):
                user.date_ad_updated = self.data['Modified']
            if self.data.get('o365_licence'):
                user.o365_licence = self.data['o365_licence']
            user.ad_data = self.data  # Store the raw request data.
            user.ad_updated = True
            # If the AD account has been deleted, update accordingly.
            if self.data.get('Deleted'):
                user.active = False
                user.ad_deleted = True
                data = list(DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS))[0]
                logger.info("Set user {} as deleted in AD\n{}".format(user.name,self.formatters.format(self.request, data)))
            user.save()
            return user
        except Exception as e:
            raise e

    def get_user(self):
        '''Return a DepartmentUser if it exists, else return None.
        Matches by AD GUID, then email, then DistinguishedName.
        '''
        if 'ObjectGUID' in self.data and \
                DepartmentUser.objects.filter(ad_guid=self.data['ObjectGUID']).exists():
            return DepartmentUser.objects.get(ad_guid=self.data['ObjectGUID'])
        if 'EmailAddress' in self.data and \
                DepartmentUser.objects.filter(email__iexact=self.data['EmailAddress']).exists():
            return DepartmentUser.objects.get(email__iexact=self.data['EmailAddress'])
        if 'email' in self.data and \
                DepartmentUser.objects.filter(email__iexact=self.data['email']).exists():
            return DepartmentUser.objects.get(email__iexact=self.data['email'])
        if 'DistinguishedName' in self.data and \
                DepartmentUser.objects.filter(ad_dn=self.data['DistinguishedName']).exists():
            return DepartmentUser.objects.get(ad_dn=self.data['DistinguishedName'])
        return None


class LocationResource(CSVDjangoResource):
    VALUES_ARGS = (
        'pk', 'name', 'address', 'phone', 'fax', 'email', 'point', 'url',
        'bandwidth_url')

    def list_qs(self):
        FILTERS = {}
        if 'location_id' in self.request.GET:
            FILTERS['pk'] = self.request.GET['location_id']
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
