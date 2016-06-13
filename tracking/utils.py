import csv
from datetime import datetime
from django.conf import settings
import logging
from openpyxl import load_workbook
import os
from StringIO import StringIO
import subprocess
import unicodecsv

from tracking.models import DepartmentUser


def logger_setup(name):
    # Ensure that the logs dir is present.
    subprocess.check_call(['mkdir', '-p', 'logs'])
    # Set up logging in a standardised way.
    logger = logging.getLogger(name)
    if settings.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:  # Log at a higher level when not in debug mode.
        logger.setLevel(logging.INFO)
    if not len(logger.handlers):  # Avoid creating duplicate handlers.
        fh = logging.handlers.RotatingFileHandler(
            'logs/{}.log'.format(name), maxBytes=5 * 1024 * 1024, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


def csv_data(csv_path):
    """Pass in the path to a CSV file, returns a CSV Reader object.
    """
    csv_file = open(csv_path, 'r')
    # Determine the CSV dialect.
    dialect = csv.Sniffer().sniff(csv_file.read(1024))
    csv_file.seek(0)
    data = csv.reader(csv_file, dialect)
    return data


def sourcefile_setup(sourcefile):
    """Read source CSV data (from source_files dir), return a csvreader object
    and a count of the rows. Assumes that data has a header.
    """
    source = os.path.join(settings.BASE_DIR, 'source_files', sourcefile)
    csvfile = open(source, 'r')
    csvcounter = csv.reader(csvfile)
    row_count = sum(1 for row in csvcounter) - 1  # Read the file to count rows
    csvfile.close()
    # Reopen the CSV.
    csvfile = open(source, 'r')
    csvreader = csv.reader(csvfile)
    csvreader.next()  # Skip the headers row.
    return csvreader, row_count


def strip_non_ascii(string):
    """Returns a string without non-ASCII characters.
    """
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)


def csv_sync_prop_register_data(src='it_assets.csv'):
    """Utility function to import local property register data from a CSV file
    (called it_assets.csv by default) saved in the source_files dir.

    Matches on serial number, should be non-destructive of existing data.
    """
    from .models import Computer
    data, count = sourcefile_setup(src)

    for i in data:
        serial = i[0].strip().upper()  # We save uppercase serials in the db.
        if serial:  # Non-blanks
            comps = Computer.objects.filter(serial_number=serial)
        else:
            comps = None
        if comps:
            # Cope with having duplicate serial numbers in Incredibus.
            for c in comps:
                if i[1]:  # Cost centre no.
                    c.cost_centre_no = int(i[1])
                if i[3]:  # Finance asset no.
                    c.finance_asset_id = i[3]
                if i[4]:  # OIM asset no.
                    c.asset_id = i[4]
                c.save()
                print('Updated {}'.format(c))
                if c.cost_centre_no:
                    c.ad_set_cost_centre()
                    print('Updated {} CC in AD'.format(c))
                if c.finance_asset_id:
                    c.ad_set_finance_asset_number()
                    print('Updated {} Finance asset no in AD'.format(c))
                if c.asset_id:
                    c.ad_set_asset_number()
                    print('Updated {} OIM asset no in AD'.format(c))

    print('Done')


def alesco_data_import(filepath):
    """Import task expects to be passed a file path to a closed .xlsx file.
    """
    logger = logger_setup('alesco_data_import')
    f = open(filepath)
    wb = load_workbook(filename=f.name, read_only=True)
    ws = wb.worksheets[0]
    keys = []
    values = []
    non_matched = 0
    multi_matched = 0
    updates = 0
    # Iterate over each row in the worksheet.
    for k, row in enumerate(ws.iter_rows()):
        values = []
        for cell in row:
            # First row: generate keys.
            if k == 0:
                keys.append(cell.value)
            # Otherwise make a list of values.
            else:
                # Serialise datetime objects.
                if isinstance(cell.value, datetime):
                    values.append(cell.value.isoformat())
                else:
                    values.append(cell.value)
        if k > 0:
            # Construct a dictionary of row values.
            record = dict(zip(keys, values))
            # Try to find a matching DepartmentUser by employee id.
            d = DepartmentUser.objects.filter(employee_id=record['EMPLOYEE_NO'])
            if d.count() > 1:
                multi_matched += 1
            elif d.count() == 1:
                d = d[0]
                d.alesco_data = record
                d.save()
                updates += 1
            else:
                non_matched += 0
    if updates > 0:
        logger.info('Alesco data for {} DepartmentUsers was updated.'.format(updates))
    if non_matched > 0:
        logger.warning('Employee ID was not matched for {} rows.'.format(non_matched))
    if multi_matched > 0:
        logger.error('Employee ID was matched for >1 DepartmentUsers for {} rows.'.format(multi_matched))

    return True


def departmentuser_csv_report():
    """Output data from all DepartmentUser objects to a CSV, unpacking the
    various JSONField values.
    Returns a StringIO object that can be written to a response or file.
    """
    FIELDS = [
        'name', 'title', 'telephone', 'mobile_phone', 'home_phone',
        'other_phone', 'email', 'employee_id', 'name_update_reference',
        'username']
    TYPE_CHOICES = {x[0]: x[1] for x in DepartmentUser.ACCOUNT_TYPE_CHOICES}

    # Get a DepartmentUser with non-null alesco_data field
    du = DepartmentUser.objects.filter(alesco_data__isnull=False)[0]
    alesco_fields = du.alesco_data.keys()
    alesco_fields.sort()

    org_fields = {
        'department': ('units', 0, 'name'),
        'division': ('units', 1, 'name'),
        'branch': ('units', 2, 'name')
    }

    header = [f for f in FIELDS]
    header.append('cost_centre')
    header.append('account_type')
    header += org_fields.keys()
    header += alesco_fields
    stream = StringIO()

    wr = unicodecsv.writer(stream, encoding='utf-8')
    wr.writerow(header)
    # Write data for all DepartmentUser objects to the CSV
    for u in DepartmentUser.objects.filter(active=True):
        record = []
        for f in FIELDS:
            record.append(getattr(u, f))
        try:
            record.append(u.cost_centre.code)
        except:
            record.append('')
        try:
            record.append(TYPE_CHOICES[u.account_type])
        except:
            record.append('')
        for o in org_fields:
            try:
                src = u.org_data
                for x in org_fields[o]:
                    src = src[x]
                record.append(src)
            except:
                record.append('')

        for a in alesco_fields:
            try:
                record.append(u.alesco_data[a])
            except:
                record.append('')
        wr.writerow(record)

    return stream.getvalue()
