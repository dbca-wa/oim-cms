from django.conf.urls import url
from django.core.exceptions import FieldError
from django.http import HttpResponseServerError

from tastypie import fields
from tastypie.api import Api
from tastypie.http import HttpBadRequest
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.authentication import SessionAuthentication
import tracking.models as models
from whippedcream.serializer import Serializer


def generate_filtering(mdl):
    """Utility function to add all model fields to filtering whitelist.
    See: http://django-tastypie.readthedocs.org/en/latest/resources.html#basic-filtering
    """
    filtering = {}
    for field in mdl._meta.fields:
        filtering.update({field.name: ALL_WITH_RELATIONS})
    return filtering


class APIResource(ModelResource):

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>{})/fields/(?P<field_name>[\w\d_.-]+)/$".format(self._meta.resource_name),
                self.wrap_view('field_values'), name="api_field_values"),
        ]

    def field_values(self, request, **kwargs):
        # Get a list of unique values for the field passed in kwargs.
        try:
            # NOTE: the distinct() function would not function as expected until
            # an empty order_by was prepended to the queryset.
            qs = self._meta.queryset.order_by().values_list(kwargs['field_name'], flat=True).distinct()
            qs = [i for i in qs if i]  # Remove 'falsy' values (i.e. None, '', etc.)
        except FieldError as e:
            return self.create_response(request, data={'error': str(e)}, response_class=HttpBadRequest)
        # Prepare and return the HttpResponse.
        return self.create_response(request, data=list(qs))


class DepartmentUserResource(APIResource):
    managed_by = fields.ToOneField('tracking.api.DepartmentUserResource', 'managed_by', null=True, readonly=True)
    disabled = fields.CharField(attribute='disabled', readonly=True)

    class Meta:
        queryset = models.DepartmentUser.objects.all()
        filtering = generate_filtering(models.DepartmentUser)


class ComputerResource(APIResource):
    probable_owner = fields.ToOneField('tracking.api.DepartmentUserResource', 'probable_owner', null=True, readonly=True)
    managed_by = fields.ToOneField('tracking.api.DepartmentUserResource', 'managed_by', null=True, readonly=True)
    location = fields.CharField(attribute='location_desc', readonly=True)

    class Meta:
        authorization = DjangoAuthorization()
        queryset = models.Computer.objects.all()
        filtering = generate_filtering(models.Computer)
        filtering['probable_owner'] = ALL_WITH_RELATIONS

    def prepend_urls(self):
        urls = super(ComputerResource, self).prepend_urls()
        # Prepend custom endpoints for this resource type.
        urls += [
            url(
                r"^(?P<resource_name>{})/(?P<pk>[^/]+)/update_cost_centre/$".format(self._meta.resource_name),
                self.wrap_view('update_cost_centre'), name="api_set_computer_cost_centre"),
            url(
                r"^(?P<resource_name>{})/(?P<pk>[^/]+)/update_asset_number/$".format(self._meta.resource_name),
                self.wrap_view('update_asset_number'), name="api_update_asset_number"),
            url(
                r"^(?P<resource_name>{})/(?P<pk>[^/]+)/update_managed_by/$".format(self._meta.resource_name),
                self.wrap_view('update_managed_by'), name="api_update_managed_by"),
            url(
                r'^(?P<resource_name>{})/security_test_results/$'.format(self._meta.resource_name),
                self.wrap_view('security_test_results'), name='api_security_test_results'),
        ]
        return urls

    def update_cost_centre(self, request, **kwargs):
        """View to allow sync of object cost centre into AD.
        """
        self.method_check(request, allowed=['post'])
        try:
            obj = models.Computer.objects.get(pk=kwargs['pk'])
        except models.Computer.DoesNotExist:
            return HttpBadRequest('Unknown computer object')
        new_cost_centre_no = request.REQUEST.get('cost_centre_no', None)
        obj.cost_centre_no = new_cost_centre_no
        obj.save()
        # If the device is linked to an AD object, ensure that the changes are
        # pushed to AD as well.
        if obj.ad_guid:  # Object is linked to AD.
            res = obj.ad_set_cost_centre()
            if not res:
                return HttpResponseServerError('Unable to update cost centre number in AD')
        return self.create_response(request, data=obj)

    def update_asset_number(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        try:
            obj = models.Computer.objects.get(pk=kwargs['pk'])
        except models.Computer.DoesNotExist:
            return HttpBadRequest('Unknown computer object')
        new_asset_no = request.REQUEST.get('asset_id', None)
        if not new_asset_no:
            new_asset_no = ''
        # If the device is linked to an AD object, ensure that the changes are
        # first pushed to AD before saving in Incredibus.
        if obj.ad_guid:  # Object is linked to AD.
            obj.asset_id = new_asset_no
            res = obj.ad_set_asset_number()  # Push the updated asset number to AD first.
            if res:
                obj.save()
                return self.create_response(request, data=obj)
            else:
                return HttpResponseServerError('Unable to update asset number in AD')
        else:  # No link to AD.
            obj.asset_id = new_asset_no
            obj.save()
            return self.create_response(request, data=obj)

    def update_managed_by(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        try:
            obj = models.Computer.objects.get(pk=kwargs['pk'])
        except models.Computer.DoesNotExist:
            return HttpBadRequest('Unknown computer object')
        new_managed_by_id = request.REQUEST.get('managed_by_id', None)
        if not new_managed_by_id:
            return HttpBadRequest('No managed_by Manager supplied')
        # If the device is linked to an AD object, ensure that the changes are
        # first pushed to AD before saving in Incredibus.
        if obj.ad_guid:  # Object is linked to AD.
            obj.managed_by_id = new_managed_by_id
            res = obj.push_managed_by()  # Push the updated managed_by to AD first.
            if res:
                obj.save()
                return self.create_response(request, data=obj)
            else:
                return HttpResponseServerError('Unable to update managed_by in AD')
        else:  # No link to AD.
            obj.managed_by_id = new_managed_by_id
            obj.save()
            return self.create_response(request, data=obj)

    def security_test_results(self, request, **kwargs):
        """Defines an endpoint that allows filtering just Computer objects
        with one or more related SecurityTestResult objects.
        """
        request.custom_filter = 'security_test_results'
        return self.dispatch_list(request)


class MobileResource(APIResource):
    registered_to = fields.ToOneField(DepartmentUserResource, 'registered_to', null=True, full=True)

    class Meta:
        authorization = DjangoAuthorization()
        queryset = models.Mobile.objects.all()
        filtering = generate_filtering(models.Mobile)
        filtering['registered_to'] = ALL_WITH_RELATIONS


v1_api = Api(api_name='v1')
v1_api.register(DepartmentUserResource())
v1_api.register(ComputerResource())
v1_api.register(MobileResource())
