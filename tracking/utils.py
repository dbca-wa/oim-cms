import csv
import os
from django.conf import settings
from tablib import Dataset
from harvest import utils_ldap
import logging
import subprocess

from .models import Computer


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


def csv_output_computers():
    """Utility function to generate a CSV output of computers information from
    Incredibus data, for audit/cleansing purposes.
    """
    computers = Computer.objects.all()
    d = Dataset()
    d.headers = [
        'ID',
        'HOSTNAME',
        'CHASSIS',
        'PROBABLE OWNER EMAIL',
        'PROBABLE OWNER CC',
        'MANAGED BY EMAIL',
        'ASSET NO.',
        'SERIAL NO.'
    ]

    for i in computers:
        row = [i.pk, i.sam_account_name[:-1], i.chassis]
        if i.probable_owner:
            row += [i.probable_owner.email.lower(), i.probable_owner.cost_centre]
        else:
            row += ['', '']
        if i.managed_by:
            row += [i.managed_by.email.lower()]
        else:
            row += ['']
        row += ['', i.serial_number]
        d.append(row)

    f = open('/tmp/computers.csv', 'w')
    f.write(d.csv)
    f.close()


def ad_users_csv():
    print('Downloading user data from AD')
    ad_users = utils_ldap.ldap_search(settings.AD_FILTER_USERS)
    f = open('/tmp/ad_users.csv', 'w')
    c = csv.writer(f)
    c.writerow(('AD DN', 'Username', 'User?', 'Admin?', 'Vendor?', 'Disabled?', 'Cost Centre', 'Description'))
    print('Outputting user data to /tmp/ad_users.csv')
    for dn, record in ad_users:
        username = record.get('sAMAccountName', ('',))[0].lower()
        is_user = 'OU=Users' in dn
        is_admin = username.endswith('-admin')
        is_vendor = 'OU=Vendor' in dn
        is_disabled = 'OU=Disabled Accounts' in dn
        cc = record.get('company', ('',))[0]
        desc = record.get('description', ('',))[0].strip()
        c.writerow((dn, username, is_user, is_admin, is_vendor, is_disabled, cc, desc))
    f.close()
