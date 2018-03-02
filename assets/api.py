from __future__ import unicode_literals, absolute_import
from django.conf.urls import url
from oim_cms.utils import CSVDjangoResource
from restless.preparers import Preparer
from restless.resources import skip_prepare

from .models import HardwareAsset


class HardwareAssetPreparer(Preparer):
    """Custom field preparer class for HardwareAssetResource.
    """
    def prepare(self, data):
        result = {
            'asset_tag': data.asset_tag,
            'finance_asset_tag': data.finance_asset_tag,
            'serial': data.serial,
            'vendor': data.vendor.name,
            'hardware_model': data.hardware_model.model_type,
            'status': data.get_status_display(),
            'notes': data.notes,
            'cost_centre': data.cost_centre.name if data.cost_centre else '',
            'location': data.location.name if data.location else '',
            'assigned_user': data.assigned_user.email if data.assigned_user else '',
            'date_purchased': data.date_purchased,
            'purchased_value': data.purchased_value,
            'is_asset': data.is_asset,
            'local_property': data.local_property,
            'warranty_end': data.warranty_end
        }
        return result


class HardwareAssetResource(CSVDjangoResource):

    def __init__(self, *args, **kwargs):
        super(HardwareAssetResource, self).__init__(*args, **kwargs)
        self.http_methods.update({
            'detail_tag': {
                'GET': 'detail_tag',
            }
        })

    preparer = HardwareAssetPreparer()

    @classmethod
    def urls(self, name_prefix=None):
        urlpatterns = super(HardwareAssetResource, self).urls(name_prefix=name_prefix)
        return [
            url(r'^(?P<asset_tag>[Ii][Tt][0-9]+)/$', self.as_view('detail_tag'), name=self.build_url_name('detail_tag', name_prefix)),
        ] + urlpatterns

    def list_qs(self):
        # By default, filter out 'Disposed' assets.
        filters = {'status__in': ['In storage', 'Deployed']}
        if 'all' in self.request.GET:
            filters.pop('status__in')
        if 'asset_tag' in self.request.GET:
            filters.pop('status__in')  # Also search disposed assets.
            filters['asset_tag__icontains'] = self.request.GET['asset_tag']
        if 'cost_centre' in self.request.GET:
            filters['cost_centre__code__icontains'] = self.request.GET['cost_centre']
        return HardwareAsset.objects.filter(**filters).prefetch_related(
            'vendor', 'hardware_model', 'cost_centre', 'location', 'assigned_user'
        )

    def list(self):
        return list(self.list_qs())

    def detail(self, pk):
        return HardwareAsset.objects.get(pk=pk)

    @skip_prepare
    def detail_tag(self, asset_tag):
        """Custom endpoint to return a single hardware asset, filterd by asset tag no.
        """
        return self.prepare(HardwareAsset.objects.get(asset_tag__istartswith=asset_tag))
