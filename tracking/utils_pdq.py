from django.utils import timezone
import os
from uuid import UUID

from tracking.models import Computer
from tracking.utils import logger_setup, csv_data


def pdq_load_hardware():
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

    for row in data:
        computer = None

        try:
            urn = UUID(row[2]).urn
        except Exception as e:
            logger_ex.error('Computer {} has invalid Active Directory GUID in PDQ Inventory {}, skipping.'.format(row[1], row[2]))
            logger_ex.info(row)
            logger_ex.exception(e)
            num_skipped += 1
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

    logger.info('Created {}, updated {}, skipped {}'.format(num_created, num_updated, num_skipped))
