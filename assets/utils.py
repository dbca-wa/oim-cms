from __future__ import unicode_literals, absolute_import
from decimal import Decimal
from dateutil.parser import parse
import re
import unicodecsv

from organisation.models import DepartmentUser, Location, CostCentre
from .models import HardwareAsset, Vendor, HardwareModel


def validate_csv(fileobj):
    """Performs validation on a CSV file of asset data.
    Returns a tuple (number of assets, errors, warnings, notes).
    """
    try:
        c = unicodecsv.DictReader(fileobj)
        c.fieldnames
    except Exception:
        errors = ["""The file you uploaded could not be interpreted. Check that
            you uploaded the correct file (in a .csv format) and try again."""]
        return (0, errors, [], [])

    critical_fields = ('asset tag', 'serial', 'date purchased')
    all_fields = critical_fields + (
        'finance asset tag', 'vendor', 'hardware model', 'location',
        'status', 'cost centre', 'purchased value', 'assigned user', 'notes')
    errors = []
    warnings = []
    notes = []
    asset_tag_list = []

    # Inspect the header row.
    for field in critical_fields:
        if field not in c.fieldnames:
            errors.append(
                'The mandatory column {} is missing from the spreadsheet.'.format(field))

    if 'status' not in c.fieldnames:
        warnings.append('''Your spreadsheet does not contain a column called
            'status' - the status field of every new asset will be set to
            'In storage'.''')

    for field in c.fieldnames:
        if field not in all_fields:
            warnings.append('''Your spreadsheet contains an unknown column '{}'.
                This column will be ignored during the import process.'''.format(field))

    # Inspect each row and do field-specific validation.
    for row in c:
        # Check asset tag.
        asset_tag_re = re.compile("^IT\d{5}$")
        if 'asset tag' in row and row['asset tag']:
            if HardwareAsset.objects.filter(asset_tag__iexact=row['asset tag']).exists():
                errors.append(
                    '''Row {}: The asset tag '{}' already exists in the database. '''
                    '''Asset tags must be unique.'''.format(c.line_num, row['asset tag']))
            if not asset_tag_re.match(row['asset tag'].upper()):
                errors.append(
                    '''Row {}: The value '{}' in the asset tag column is '''
                    '''invalid. Asset tags should be in the format '''
                    '''ITXXXXX.'''.format(c.line_num, row['asset tag']))
            if row['asset tag'].upper() in asset_tag_list:
                errors.append(
                    '''Row {}: The asset tag '{}' exists in several rows in '''
                    '''the spreadsheet. Asset tags are unique - remove the '''
                    '''duplicate values to continue.'''.format(c.line_num, row['asset tag']))
            asset_tag_list.append(row['asset tag'].upper())
        else:
            errors.append(
                '''Row {}: A value for the asset tag column is missing. '''
                '''Enter a value to continue.'''.format(c.line_num))

        # Check serial.
        if 'serial' in row and not row['serial']:
            errors.append(
                '''Row {}: The mandatory field 'serial' is blank. If the '''
                '''hardware does not have a serial, enter 'Unknown'.'''.format(c.line_num))

        # Check date purchased.
        if 'date purchased' in row and row['date purchased']:
            try:
                parse(row['date purchased'])
            except ValueError:
                errors.append(
                    '''Row {}: The value '{}' in the 'date purchased' column '''
                    '''is invalid. Dates must be in the format '''
                    '''dd/mm/yyyy.'''.format(c.line_num, row['date purchased']))
        else:
            errors.append(
                '''Row {}: The mandatory field 'date purchased' is blank.'''.format(c.line_num))

        # Check finance asset tag.
        if 'finance asset tag' in row and row['finance asset tag']:
            finance_asset_tag_re = re.compile("^\d+$")
            if not finance_asset_tag_re.match(row['finance asset tag']):
                warnings.append(
                    '''Row {}: The finance asset tag '{}' contains numbers '''
                    '''and other characters - these tags usually only contain '''
                    '''numbers. Check the tag is correct before '''
                    '''proceeding.'''.format(c.line_num, row['finance asset tag']))

        # Check vendor.
        if 'vendor' in row and row['vendor']:
            if not Vendor.objects.filter(name__iexact=row['vendor']).exists():
                notes.append(
                    '''Row {}: Vendor '{}' is unknown - a new vendor '''
                    '''will be created.'''.format(c.line_num, row['vendor']))

        # Check hardware model.
        if 'hardware model' in row and row['hardware model']:
            if not HardwareModel.objects.filter(model_no__iexact=row['hardware model']).exists():
                notes.append(
                    '''Row {}: Model '{}' is unknown - a new model will '''
                    '''be created.'''.format(c.line_num, row['hardware model']))

        # Check status.
        if 'status' in row and row['status']:
            if row['status'] not in ['In storage', 'Deployed', 'Disposed']:
                errors.append(
                    '''Row {}: The value '{}' in the status column is invalid. '''
                    '''The asset status must be one of 'In storage', '''
                    ''''Deployed' or 'Disposed'.'''.format(c.line_num, row['status']))

        # Check cost centre.
        if 'cost centre' in row and row['cost centre']:
            if CostCentre.objects.filter(code=row['cost centre']) < 1:
                errors.append(
                    '''Row {}: There is no cost centre code that matches {}. '''
                    '''Cost centre must exactly match existing codes.'''.format(c.line_num, row['cost centre']))
        # Check location.
        if 'location' in row and row['location']:
            if Location.objects.filter(name__istartswith=row['location']).count() > 1:
                errors.append(
                    '''Row {}: {} matches more than one location name. '''
                    '''Locations must match existing names.'''.format(c.line_num, row['location']))
            elif Location.objects.filter(name__istartswith=row['location']).count() < 1:
                errors.append(
                    '''Row {}: There is no location matching name {}. '''
                    '''Locations must match existing names.'''.format(c.line_num, row['location']))

    # Reset fileobj now that we're finished with it.
    fileobj.seek(0)
    return (len(asset_tag_list), errors, warnings, notes)


def import_csv(fileobj):
    """Undertakes an import of the passed-in CSV file.
    Returns a list of objects created.
    """
    c = unicodecsv.DictReader(fileobj)
    unknown_vendor = Vendor.objects.get_or_create(name='Unknown Vendor')[0]
    unknown_model = HardwareModel.objects.get_or_create(
        model_type='Other', vendor=unknown_vendor, model_no='Unknown model',
        lifecycle=3)[0]
    unknown_location = Location.objects.get_or_create(
        name='Unknown', address='Unknown')[0]
    assets_created = []

    for row in c:
        asset = HardwareAsset(
            asset_tag=row['asset tag'].upper(), serial=row['serial'],
            date_purchased=parse(row['date purchased'])
        )
        if 'finance asset tag' in row and row['finance asset tag']:
            asset.finance_asset_tag = row['finance asset tag']
        if 'vendor' in row and row['vendor']:
            if not Vendor.objects.filter(name__iexact=row['vendor']).exists():
                vendor = Vendor.objects.get_or_create(name=row['vendor'])[0]
                asset.vendor = vendor
            else:
                vendor = Vendor.objects.get(name__iexact=row['vendor'])
                asset.vendor = vendor
        else:
            # No vendor specified.
            asset.vendor = unknown_vendor

        if 'hardware model' in row and row['hardware model']:
            if not HardwareModel.objects.filter(model_no__iexact=row['hardware model']).exists():
                # Create a new hardware model (use the vendor as manufacturer).
                asset.hardware_model = HardwareModel.objects.get_or_create(
                    vendor=asset.vendor, model_no=row['hardware model'], model_type='Other',
                    lifecycle=3)[0]
            else:
                # Use the existing hardware model.
                asset.hardware_model = HardwareModel.objects.get(model_no__iexact=row['hardware model'])
        else:
            # No hardware model specified.
            asset.hardware_model = unknown_model

        if 'location' in row and row['location']:
            if Location.objects.filter(name__istartswith=row['location']).count() == 1:
                asset.location = Location.objects.get(name__istartswith=row['location'])
            else:
                asset.location = unknown_location
        if 'status' in row and row['status']:
            if row['status'] in ['In storage', 'Deployed', 'Disposed']:
                asset.status = row['status']
        if 'cost centre' in row and row['cost centre']:
            try:
                asset.cost_centre = CostCentre.objects.get(code=row['cost centre'])
            except:
                asset.cost_centre = None
        if 'purchased value' in row and row['purchased value']:
            try:
                asset.purchased_value = Decimal(row['purchased value'])
            except:
                asset.purchased_value = None
        if 'assigned user' in row and row['assigned user']:
            if DepartmentUser.objects.filter(username__iexact=row['assigned user']).exists():
                asset.assigned_user = DepartmentUser.objects.get(
                    username__iexact=row['assigned user'])
        if 'notes' in row and row['notes']:
            asset.notes = row['notes']
        asset.save()
        assets_created.append(asset)

    return assets_created


def humanise_age(d):
    """Passed in a timedelta objects, this funciton returns a nice age like "25 days" or
    "3 months", with appropriate resolution.
    """
    if d.days >= 730:
        years = d.days/365
        months = (d.days - years*365)/30
        if months > 0:
            return "%d years, %d months" % (years, months)
        else:
            return "%d years" % (years)
    elif d.days >= 365:
        months = (d.days - 365)/30
        if months > 0:
            return "1 year, %d months" % (months)
        else:
            return "1 year"
    elif d.days >= 60:
        return "%d months" % (d.days/30)
    elif d.days >= 30:
        return "1 month"
    elif d.days >= 2:
        return "%d days" % (d.days)
    elif d.days == 1:
        return "1 day"
    elif d.seconds >= 7200:
        return "%d hours" % (d.seconds/3600)
    elif d.seconds >= 3600:
        return "1 hour"
    elif d.seconds >= 120:
        return "%d minutes" % (d.seconds/60)
    elif d.seconds >= 60:
        return "1 minute"
    elif d.seconds >= 2:
        return "%s seconds" % (d.seconds)
    elif d.seconds == 0:
        # Things exactly the same are probably date objects, so max. 1-day
        # resolution
        return "1 day"
    else:
        return "1 second"
