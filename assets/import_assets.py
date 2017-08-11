from __future__ import unicode_literals, absolute_import, print_function

from datetime import datetime
import json
from organisation.models import DepartmentUser, Location
from .models import Vendor, HardwareModel, Invoice, HardwareAsset


def import_assets():
    """Import assets from a dumped JSON fixture. Dump command:
    python manage.py dumpdata --format json --indent=4 --natural-foreign --natural-primary -o assets.json assets
    """
    data = json.loads(open('assets.json', 'r').read())
    suppliers = {}
    models = {}
    locations = {}
    invoices = {}
    assets = {}

    for obj in data:
        if obj['model'] == 'assets.supplier':
            suppliers[obj['pk']] = obj['fields']
        elif obj['model'] == 'assets.model':
            models[obj['pk']] = obj['fields']
        elif obj['model'] == 'assets.location':
            locations[obj['pk']] = obj['fields']
        elif obj['model'] == 'assets.invoice':
            invoices[obj['pk']] = obj['fields']
        elif obj['model'] == 'assets.asset':
            assets[obj['pk']] = obj['fields']

    assets_history = json.loads(open('assets_history.json', 'r').read())

    for d in suppliers.itervalues():
        if Vendor.objects.filter(name=d['name']).exists():
            vendor = Vendor.objects.get(name=d['name'])
        else:
            vendor = Vendor(name=d['name'])
        vendor.details = d['notes']
        vendor.account_rep = d['account_rep']
        vendor.contact_email = d['contact_email']
        vendor.contact_phone = d['contact_phone']
        vendor.website = d['website']
        vendor.save()

    for d in models.itervalues():
        vendor = Vendor.objects.get(name=suppliers[d['manufacturer']]['name'])
        if HardwareModel.objects.filter(model_type=d['model_type'], vendor=vendor, model_no=d['model']).exists():
            hwmodel = HardwareModel.objects.get(model_type=d['model_type'], vendor=vendor, model_no=d['model'])
        else:
            hwmodel = HardwareModel(model_type=d['model_type'], vendor=vendor, model_no=d['model'])
        hwmodel.lifecycle = d['lifecycle']
        hwmodel.notes = d['notes']
        hwmodel.save()

    for d in invoices.itervalues():
        vendor = Vendor.objects.get(name=suppliers[d['supplier']]['name'])
        if Invoice.objects.filter(vendor=vendor, job_number=d['job_number']).exists():
            invoice = Invoice.objects.get(vendor=vendor, job_number=d['job_number'])
        else:
            invoice = Invoice(vendor=vendor, job_number=d['job_number'])
        invoice.vendor_ref = d['supplier_ref']
        if d['date']:
            invoice.date = datetime.strptime(d['date'], '%Y-%m-%d')
        invoice.etj_number = d['etj_number']
        invoice.total_value = d['total_value']
        invoice.notes = d['notes']
        invoice.save()

    for k, d in assets.iteritems():
        if HardwareAsset.objects.filter(asset_tag=d['asset_tag']).exists():
            hwasset = HardwareAsset.objects.get(asset_tag=d['asset_tag'])
        else:
            hwasset = HardwareAsset(asset_tag=d['asset_tag'])
        hwasset.finance_asset_tag = d['finance_asset_tag']
        vendor = Vendor.objects.get(name=suppliers[models[d['model']]['manufacturer']]['name'])
        hwasset.vendor = vendor
        hwasset.date_purchased = datetime.strptime(d['date_purchased'], '%Y-%m-%d')
        hwasset.purchased_value = d['purchased_value']
        if d['invoice']:
            try:
                hwasset.invoice = Invoice.objects.get(vendor=vendor, job_number=invoices[d['invoice']]['job_number'])
            except:
                pass
        hwasset.hardware_model = HardwareModel.objects.get(
            model_type=models[d['model']]['model_type'], model_no=models[d['model']]['model'],
            vendor=vendor)
        hwasset.status = d['status']
        hwasset.serial = d['serial']
        hwasset.notes = d['notes']
        loc = locations[d['location']]
        hwasset.extra_data = {}
        hwasset.extra_data['location'] = 'Name: {}, block: {}, site: {}'.format(loc['name'], loc['block'], loc['site'])
        hwasset.extra_data['assigned_user'] = d['assigned_user']
        hwasset.extra_data['revision_history'] = []
        # Revision history
        if str(k) in assets_history:
            hwasset.extra_data['revision_history'] = assets_history[str(k)]
        hwasset.save()


def asset_assigned_user():
    """Run after importing legacy assets - tries to match assigned user to DepartmentUser.
    """
    for i in HardwareAsset.objects.all():
        if i.extra_data and 'assigned_user' in i.extra_data and i.extra_data['assigned_user']:
            user = i.extra_data['assigned_user']
            if DepartmentUser.objects.filter(username__iexact=user).exists():
                i.assigned_user = DepartmentUser.objects.get(username__iexact=user)
                i.save()
            elif DepartmentUser.objects.filter(name__iexact=user).exists():
                i.assigned_user = DepartmentUser.objects.get(name__iexact=user)
                i.save()


def asset_location():
    """Run after importing legacy assets - tries to match location to Location.
    """
    kens = Location.objects.get(name='Kensington (State Headquarters)')
    burvill = Location.objects.get(name='Kensington (Burvill Court)')

    for i in HardwareAsset.objects.all():
        if i.extra_data and 'location' in i.extra_data:
            loc = i.extra_data['location'].split(', ')
            d = {}

            try:
                for j in loc:
                    k, v = j.split(': ')
                    d[k.lower()] = v
                locations = Location.objects.filter(name__istartswith=d['site'])
                if locations.count() > 1:
                    # Kensington or Burvill Court
                    if 'Burvill' in d['block'] or d['block'] == 'Radio Communications Section':
                        i.location = burvill
                    else:
                        i.location = kens
                    i.save()
                elif locations.count() == 1:
                    i.location = locations.first()
                    i.save()
            except:
                pass


def export_asset_revisions():
    asset_history = {}

    for a in Asset.objects.all():
        history = []
        for v in Version.objects.get_for_object(a).order_by('id'):
            history.append({
                'date': datetime.strftime(v.revision.date_created, '%Y-%b-%d %H:%M'),
                'user': v.revision.user.username,
                'comment': v.revision.comment,
                'data': v.serialized_data})
            asset_history[a.pk] = history

        f = open('assets_history.json', 'w')
        f.write(json.dumps(asset_history))
