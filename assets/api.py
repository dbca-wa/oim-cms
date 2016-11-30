from __future__ import unicode_literals, absolute_import
from oim_cms.utils import CSVDjangoResource
from restless.preparers import Preparer

from .models import HardwareAsset


class HardwareAssetPreparer(Preparer):
    """Custom field preparer class for HardwareAssetResource.
    """
    def prepare(self, data):
        result = {
            'vendor': data.vendor.name,
            'date_purchased': data.date_purchased,
            'purchased_value': data.purchased_value,
            'notes': data.notes,
            'asset_tag': data.asset_tag,
            'finance_asset_tag': data.finance_asset_tag,
            'hardware_model': data.hardware_model.model_type,
            'status': data.get_status_display(),
            'serial': data.serial,
            'location': str(data.location) if data.location else '',
            'assigned_user': data.assigned_user.email if data.assigned_user else ''
        }
        return result


class HardwareAssetResource(CSVDjangoResource):

    preparer = HardwareAssetPreparer()

    def list(self):
        return HardwareAsset.objects.all()
