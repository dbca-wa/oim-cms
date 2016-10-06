from __future__ import unicode_literals, absolute_import
from django.conf import settings
from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseBadRequest)
from django.utils.text import slugify
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
import json
from restless.dj import DjangoResource
from restless.resources import skip_prepare
from restless.utils import MoreTypesJSONEncoder
from oim_cms.utils import FieldsFormatter

from .models import DepartmentUser, Location, SecondaryLocation, OrgUnit, CostCentre


ACCOUNT_TYPE_DICT = dict(DepartmentUser.ACCOUNT_TYPE_CHOICES)


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
        'mobile_phone', 'photo', 'photo_ad', 'org_data', 'parent__email',
        'parent__name', 'username', 'org_unit__location__id',
        'org_unit__location__name', 'org_unit__location__address',
        'org_unit__location__pobox', 'org_unit__location__phone',
        'org_unit__location__fax', 'ad_guid',
        'org_unit__secondary_location__name', 'preferred_name')
    VALUES_ARGS = COMPACT_ARGS + (
        'ad_dn', 'ad_data', 'date_updated', 'date_ad_updated', 'active',
        'ad_deleted', 'in_sync', 'given_name', 'surname', 'home_phone',
        'other_phone', 'notes', 'working_hours', 'position_type',
        'account_type')
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
        sync_o365 = True
        if 'sync_o365' in self.request.GET and self.request.GET['sync_o365'] == 'false':
            sync_o365 = False
        else:
            sync_o365 = True
        if 'populate_groups' in self.request.GET and self.request.GET['populate_groups'] == 'true':
            exclude_populate_groups = True  # Will exclude populate_primary_group == False
        else:
            exclude_populate_groups = False  # Will ignore populate_primary_group
        if 'org_structure' in self.request.GET:
            return self.org_structure(sync_o365=sync_o365, exclude_populate_groups=exclude_populate_groups)

        if 'all' in self.request.GET:
            users = DepartmentUser.objects.all().order_by('name')
        else:
            FILTERS = DepartmentUser.ACTIVE_FILTER.copy()
            # Filters below are exclusive.
            if 'email' in self.request.GET:
                FILTERS['email__iexact'] = self.request.GET['email']
            elif 'ad_guid' in self.request.GET:
                FILTERS['ad_guid__endswith'] = self.request.GET['ad_guid']
            elif 'cost_centre' in self.request.GET:
                FILTERS['cost_centre__code'] = self.request.GET['cost_centre']
            # Exclude shared and role-based account types.
            users = DepartmentUser.objects.filter(**FILTERS).exclude(account_type__in=[5, 9]).order_by('name')

        # Parameters to modify the API output.
        if 'compact' in self.request.GET:
            self.VALUES_ARGS = self.COMPACT_ARGS
        elif 'minimal' in self.request.GET:
            self.VALUES_ARGS = self.MINIMAL_ARGS

        user_values = list(users.values(*self.VALUES_ARGS))

        return self.formatters.format(self.request, user_values)

    @skip_prepare
    def create(self):
        try:
            try:
                user = DepartmentUser.objects.get(
                    email__iexact=self.data['EmailAddress'])
            except:
                try:
                    user = DepartmentUser.objects.get(
                        ad_guid__iendswith=self.data['ObjectGUID'])
                except:
                    try:
                        user = DepartmentUser.objects.get(
                            ad_dn=self.data['DistinguishedName'])
                    except:
                        user = DepartmentUser(ad_guid=self.data['ObjectGUID'])
            if self.data.get('Deleted'):
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
                user._meta.get_field_by_name('date_updated')[0].clean(
                    self.data['Modified'], user))
            if not user.pk or not user.date_ad_updated or modified > user.date_updated:
                user.email = self.data['EmailAddress']
                user.ad_guid = self.data['ObjectGUID']
                user.ad_dn = self.data['DistinguishedName']
                user.username = self.data['SamAccountName']
                user.expiry_date = self.data.get('AccountExpirationDate')
                user.active = self.data['Enabled']
                user.ad_deleted = False
                user.ad_data = self.data
                if not user.name:
                    user.name = self.data['Name']
                if not user.title:
                    user.title = self.data['Title']
                if not user.given_name:
                    user.given_name = self.data['GivenName']
                if not user.surname:
                    user.surname = self.data['Surname']
                user.date_ad_updated = self.data['Modified']
                user.ad_updated = True
                user.save()
            data = list(
                DepartmentUser.objects.filter(
                    pk=user.pk).values(
                    *self.VALUES_ARGS))[0]
        except Exception as e:
            data = self.data
            data['Error'] = repr(e)
        return self.formatters.format(self.request, data)


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
        if 'other_phone' in request.POST:
            user.other_phone = request.POST['other_phone']
        if 'preferred_name' in request.POST:
            user.preferred_name = request.POST['preferred_name']
        user.save()
        data = DepartmentUser.objects.filter(pk=user.pk).values(*self.VALUES_ARGS)[0]
    return HttpResponse(json.dumps(
        {'objects': [self.formatters.format(request, data)]}, cls=MoreTypesJSONEncoder))
