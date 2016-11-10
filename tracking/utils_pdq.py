from __future__ import absolute_import
from django.utils import timezone
import os
import unicodecsv
from uuid import UUID

from .models import Computer
from .utils import logger_setup


def csv_data(csv_path, skip_header=True):
    """Pass in the path to a CSV file, returns a CSV Reader object.
    """
    csv_file = open(csv_path, 'r')
    # Determine the CSV dialect.
    dialect = unicodecsv.Sniffer().sniff(csv_file.read(1024))
    csv_file.seek(0)
    data = unicodecsv.reader(csv_file, dialect)
    if skip_header:
        data.next()
    return data


def pdq_load_computers():
    """Update the database with Computer information from PDQ Inventory.
    Also create matching Hardware objects in the register application, if
    required.
    """
    from registers.models import Hardware
    logger = logger_setup('pdq_load_computers')
    logger_ex = logger_setup('exceptions_pdq_load_computers')
    update_time = timezone.now()
    csv_path = os.path.join(os.environ.get('PDQ_INV_PATH'), 'pdq_computers.csv')
    data = csv_data(csv_path)
    num_created = 0
    num_updated = 0
    num_skipped = 0
    num_errors = 0

    for row in data:
        try:
            computer = None
            try:
                urn = UUID(row[2]).urn
            except Exception as e:
                logger_ex.error('Computer {} has invalid Active Directory GUID in PDQ Inventory {}, skipping.'.format(row[1], row[2]))
                logger_ex.info(row)
                logger_ex.exception(e)
                num_errors += 1
                continue

            # First, try and match AD GUID.
            if urn and row[2]:
                try:
                    computer = Computer.objects.get(ad_guid=urn)
                    num_updated += 1
                except Computer.DoesNotExist:
                    pass
            # Second, try and match AD DN.
            if computer is None and row[3]:
                try:
                    computer = Computer.objects.get(ad_dn=row[3])
                    num_updated += 1
                except Computer.DoesNotExist:
                    pass
            # Third, try to match via pdq_id value.
            if computer is None and row[0]:
                try:
                    computer = Computer.objects.get(pdq_id=row[0])
                    num_updated += 1
                except Computer.DoesNotExist:
                    pass
            # Last, try to match via sAMAccountName. If no match, skip the record.
            if computer is None:
                sam = '{}$'.format(row[1].upper())
                try:
                    computer = Computer.objects.get(sam_account_name=sam)
                    num_updated += 1
                except Computer.DoesNotExist:
                    logger.info('No match for Computer object with SAM ID {} creating new object'.format(sam))
                    computer = Computer(sam_account_name=sam)
                    num_created += 1
                    pass

            computer.domain_bound = True
            computer.hostname = row[17]
            computer.pdq_id = int(row[0])
            computer.ad_guid = urn
            computer.ad_dn = row[3]
            computer.manufacturer = row[5]
            computer.model = row[6]
            computer.chassis = row[7]
            computer.serial_number = row[8]
            computer.os_name = row[9]
            computer.os_version = row[10]
            computer.os_service_pack = row[11]
            computer.os_arch = row[12]
            computer.cpu = row[13]
            computer.cpu_count = row[14]
            computer.cpu_cores = row[15]
            computer.memory = row[16]
            computer.date_pdq_updated = update_time
            computer.save()
            logger.info('Computer {} updated from PDQ Inventory scan data'.format(computer))
            try:
                hw = computer.hardware
            except Hardware.DoesNotExist:
                # Check if the host already exists.
                if Hardware.objects.filter(name__icontains=computer.hostname).exists():
                    hw = Hardware.objects.get(name__icontains=computer.hostname)
                    hw.computer = computer
                    hw.save()
                else:
                    hw = Hardware.objects.create(device_type=3, computer=computer, name=computer.hostname)
        except Exception as e:
            logger_ex.error('Error while loading computers from PDQ')
            logger_ex.info(row)
            logger_ex.exception(e)
            num_errors += 1
            continue

    logger.info('Created {}, updated {}, skipped {}, errors {}'.format(num_created, num_updated, num_skipped, num_errors))
