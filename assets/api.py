from __future__ import unicode_literals, absolute_import
from oim_cms.utils import CSVDjangoResource
from restless.preparers import Preparer

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

    preparer = HardwareAssetPreparer()

    def list(self):
        return HardwareAsset.objects.all()

    def detail(self, pk):
        return HardwareAsset.objects.get(pk=pk)
