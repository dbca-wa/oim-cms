import json
import unicodecsv as csv
import uuid
from organisation.models import DepartmentUser, OrgUnit, CostCentre, Location
from registers.models import ITSystem


def generate_new_org_units():
    """Generate new OrgUnit objects.
    """
    dbca, created = OrgUnit.objects.get_or_create(name='Department of Biodiversity, Conservation and Attractions', unit_type=0, acronym='DBCA')
    print('{} created'.format(dbca))
    pws, created = OrgUnit.objects.get_or_create(name='Parks and Wildlife Service', unit_type=1, parent=dbca)
    print('{} created'.format(pws))

    # BGPA and branches
    bgpa, created = OrgUnit.objects.get_or_create(name='Botanic Gardens and Parks Authority', unit_type=1, parent=dbca)
    for i in [
            'Business and Visitor Services',
            'Horticulture and Conservation',
            'Science',
            'Office of the Chief Executive Officer',
            'Friends of Kings Park']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=2, parent=bgpa)
        print('{} created'.format(ou))
    bvs = OrgUnit.objects.get(name='Business and Visitor Services')
    for i in ['Business and Finance', 'Aspects of Kings Park', 'Online Communications', 'Education', 'Communications (BGPA)', 'Events', 'Park Management', 'Volunteers']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=bvs)
        print('{} created'.format(ou))
    hc = OrgUnit.objects.get(name='Horticulture and Conservation')
    for i in ['Technical Services', 'Information Services', 'Plant Development', 'Kings Park Bushland', 'Bold Park Bushland', 'Horticultural Displays', 'Grounds and Infrastructure', 'Nursery', 'Arboriculture']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=hc)
        print('{} created'.format(ou))

    # RIA and branches
    ria, created = OrgUnit.objects.get_or_create(name='Rottnest Island Authority', unit_type=1, parent=dbca)
    for i in [
            'Corporate Services',
            'Destination Marketing and Visitor Experience',
            'Environment, Heritage and Parks',
            'Project and Contract Services',
            'Executive Services']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=2, parent=ria)
        print('{} created'.format(ou))
    cs = OrgUnit.objects.get(name='Corporate Services')
    for i in ['Planning and Governance', 'Corporate Finance and Procurement', 'Human Resources (RIA)', 'Information and Communications Technology', 'Commercial Operations']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=cs)
        print('{} created'.format(ou))
    ehp = OrgUnit.objects.get(name='Environment, Heritage and Parks')
    for i in ['Enviromental Services', 'Park Services', 'Conservation']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=ehp)
        print('{} created'.format(ou))
    dm = OrgUnit.objects.get(name='Destination Marketing and Visitor Experience')
    for i in ['Marketing', 'Events and Functions', 'Visitor Experience', 'Reservations', 'Pedal and Flipper']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=dm)
        print('{} created'.format(ou))

    # Zoo and branches
    zoo, created = OrgUnit.objects.get_or_create(name='Zoological Parks Authority', unit_type=1, parent=dbca)
    for i in [
            'Executive',
            'Animal Health and Research',
            'Community Engagement',
            'Finance',
            'Life Sciences',
            'People and Business Services']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=2, parent=zoo)
        print('{} created'.format(ou))
    pbs = OrgUnit.objects.get(name='People and Business Services')
    for i in ['People Services (Zoo)', 'Information Communication Technology', 'Records', 'Reception']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=pbs)
        print('{} created'.format(ou))
    ce = OrgUnit.objects.get(name='Community Engagement')
    for i in ['Partnerships', 'Visitor Services', 'Retail', 'Customer Services', 'Security and Visitors', 'Visitor Engagement and Marketing', 'Discovery and Learning', 'Business Development', 'Media and Communications']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=ce)
        print('{} created'.format(ou))
    ls = OrgUnit.objects.get(name='Life Sciences')
    for i in ['Life Sciences Operations', 'Species Management and Planning', 'Animal Records']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=ls)
        print('{} created'.format(ou))
    ahr = OrgUnit.objects.get(name='Animal Health and Research')
    for i in ['Procurement', 'Facilities and Environment Admin', 'Assets and Contracts', 'Presentation and Horticulture', 'Veterinary Department', 'Native Species Breeding Program', 'Research']:
        ou, created = OrgUnit.objects.get_or_create(name=i, unit_type=7, parent=ahr)
        print('{} created'.format(ou))


def generate_new_ccs():
    """Generate new CostCentre objects.
    """
    # Zoo
    ccs = [20, 40, 41, 43, 48, 63, 67, 73, 74, 75, 77, 78, 80, 81, 82, 84, 85, 86, 87, 88, 90, 91, 93, 94]
    for cc in ccs:
        new_cc, created = CostCentre.objects.get_or_create(code='PZ{}'.format(cc))
        print('{} created'.format(new_cc))

    # RIA
    ccs = [21, 30, 31, 32, 34, 35, 40, 50, 52, 54, 58, 61, 65, 71, 72, 80, 81, 83, 84, 85]
    for cc in ccs:
        new_cc, created = CostCentre.objects.get_or_create(code='RIA{}'.format(cc))
        print('{} created'.format(new_cc))

    # BGPA
    ccs = [
        '1110300', '1110400', '1110600', '1111100', '1120100', '1130100', '1130100',
        '1130300', '1130303', '1130500', '1140100', '1140102', '1140200', '1140300',
        '1140700', '1141000', '1141100', '1150100', '1250400', '1610000']
    for cc in ccs:
        new_cc, created = CostCentre.objects.get_or_create(code=cc, name=cc)
        print('{} created'.format(new_cc))


def join_cc_to_orgunit():
    d = {
        # Zoo
        'Life Sciences': 'PZ40',
        'Life Sciences Operations': 'PZ41',
        'Native Species Breeding Program': 'PZ48',
        'Business Development': 'PZ63',
        'Retail': 'PZ67',
        'Executive': 'PZ73',
        'People and Business Services': 'PZ74',
        'People Services (Zoo)': 'PZ75',
        'Finance': 'PZ77',
        'Partnerships': 'PZ78',
        'Community Engagement': 'PZ80',
        'Media and Communications': 'PZ81',
        'Discovery and Learning': 'PZ82',
        'Visitor Services': 'PZ84',
        'Security and Visitors': 'PZ85',
        'Assets and Contracts': 'PZ86',
        'Presentation and Horticulture': 'PZ87',
        'Procurement': 'PZ88',
        'Animal Health and Research': 'PZ90',
        'Veterinary Department': 'PZ91',
        'Research': 'PZ93',
        # BGPA
        'Business and Finance': '1110400',
        'Aspects of Kings Park': '1610000',
        'Online Communications': '1111100',
        'Education': '1130500',
        'Communications (BGPA)': '1110600',
        'Park Management': '1130100',
        'Volunteers': '1130300',
        'Technical Services': '1140100',
        'Information Services': '1140102',
        'Plant Development': '1140200',
        'Kings Park Bushland': '1150100',
        'Bold Park Bushland': '1250400',
        'Horticultural Displays': '1140300',
        'Grounds and Infrastructure': '1141000',
        'Nursery': '1141100',
        'Arboriculture': '1140700',
        'Office of the Chief Executive Officer': '1110300',
        'Friends of Kings Park': '1130303',
        # RIA
        'Reservations': 'RIA21',
        'Visitor Experience': 'RIA30',
        'Pedal and Flipper': 'RIA31',
        'Events and Functions': 'RIA34',
        'Marketing': 'RIA35',
        'Commercial Operations': 'RIA40',
        'Environment, Heritage and Parks': 'RIA50',
        'Park Services': 'RIA52',
        'Conservation': 'RIA54',
        'Project and Contract Services': 'RIA61',
        'Destination Marketing and Visitor Experience': 'RIA65',
        'Executive Services': 'RIA71',
        'Corporate Services': 'RIA80',
        'Corporate Finance and Procurement': 'RIA81',
        'Human Resources (RIA)': 'RIA83',
        'Information and Communications Technology': 'RIA84',
    }

    for name, code in d.iteritems():
        ou = OrgUnit.objects.get(name=name)
        cc = CostCentre.objects.get(code=code)
        cc.org_position = ou
        cc.save()
        print('{} updated'.format(cc))


def import_users_csv():
    for csvfile in ['RIA_all_users_list.csv', 'Zoo_all_users_list.csv', 'BGPA_all_users_list.csv']:
        f = open(csvfile, 'r')
        dialect = csv.Sniffer().sniff(f.read(4096))
        f.seek(0)
        reader = csv.reader(f, dialect=dialect)
        keys = reader.next()

        for row in reader:
            user = dict(zip(keys, row))

            if not DepartmentUser.objects.filter(email=user['EmailAddress']).exists():
                du = DepartmentUser(email=user['EmailAddress'])
                existing = False
            else:
                du = DepartmentUser.objects.get(email=user['EmailAddress'])
                existing = True
            du.active = True

            # Username needs to be unique.
            if not DepartmentUser.objects.filter(username=user['SamAccountName']).exists():
                du.username = user['SamAccountName']
            else:  # Make it FirstnameLastname
                du.username = '{}{}'.format(user['GivenName'], user['Surname'])
                if not existing:
                    print('Created {} with a different username'.format(du.email))
            du.given_name = user['GivenName']
            du.surname = user['Surname']
            du.name = '{}, {}'.format(user['Surname'], user['GivenName'])
            du.title = user['Title']
            du.telephone = user['OfficePhone']
            du.mobile_phone = user['MobilePhone']
            du.ad_dn = str(uuid.uuid4())  # Just fake it until we unify AD.

            if user['EmployeeNumber']:  # Avoid duplicates.
                if 'rottnestisland' in du.email:
                    du.employee_id = 'RIA{}'.format(user['EmployeeNumber'])
                elif 'perthzoo' in du.email:
                    du.employee_id = 'PZ{}'.format(user['EmployeeNumber'])
                elif 'bgpa' in du.email:
                    du.employee_id = 'BGPA{}'.format(user['EmployeeNumber'])

            if 'Full-time' in user['Employee Type'] or 'Fulltime' in user['Employee Type']:
                du.position_type = 0
            elif 'Part-time' in user['Employee Type'] or 'Parttime' in user['Employee Type']:
                du.position_type = 1
            elif 'Casual' in user['Employee Type']:
                du.position_type = 2
            elif 'contractor' in user['Employee Type']:
                du.contractor = True

            if 'Permanent' in user['Employee Type']:
                du.account_type = 2
            elif 'Temporary' in user['Employee Type']:
                du.account_type = 0

            du.save()

            # Cost centre
            if 'perthzoo' in du.email:
                if CostCentre.objects.filter(code='PZ{}'.format(user['CostCentre'])).exists():
                    du.cost_centre = CostCentre.objects.get(code='PZ{}'.format(user['CostCentre']))
                    du.org_unit = du.cost_centre.org_position
                    print('Linked CC {}'.format(du.cost_centre))
            elif 'rottnestisland' in du.email:
                if CostCentre.objects.filter(code='RIA{}'.format(user['CostCentre'])).exists():
                    du.cost_centre = CostCentre.objects.get(code='RIA{}'.format(user['CostCentre']))
                    print('Linked CC {}'.format(du.cost_centre))
            elif 'bgpa' in du.email:
                if CostCentre.objects.filter(code='{}'.format(user['CostCentre'])).exists():
                    du.cost_centre = CostCentre.objects.get(code=user['CostCentre'])
                    print('Linked CC {}'.format(du.cost_centre))

            # Update OrgUnit Location.
            if du.org_unit and not du.org_unit.location and user['org_unit__location__name']:
                loc, created = Location.objects.get_or_create(name=user['org_unit__location__name'], address=user['org_unit__location__address'])
                du.org_unit.location = loc
                du.org_unit.save()
                print('{} location updated'.format(du.org_unit))

            # Finally, save the whole CSV in extra_data
            du.extra_data = json.dumps(user)

            du.save()
            print('Saved {}'.format(du))


def import_it_systems_csv():
    f = open('IT_Systems_DBCA.csv', 'r')
    dialect = csv.Sniffer().sniff(f.read(4096))
    f.seek(0)
    reader = csv.reader(f, dialect=dialect)
    keys = reader.next()

    for row in reader:
        sys = dict(zip(keys, row))

        if not ITSystem.objects.filter(name=sys['Name']).exists():
            it = ITSystem(name=sys['Name'])
        else:
            it = ITSystem.objects.get(name=sys['Name'])

        it.status = 0

        if sys['System type'] == 'System - Web application':
            it.system_type = 1
        elif sys['System type'] == 'System - Client application':
            it.system_type = 2
        elif sys['System type'] == 'Service':
            it.system_type = 4

        if sys['Authentication'] == 'Domain/application credentials':
            it.authentication = 1
        elif sys['Authentication'] == 'Single Sign-On':
            it.authentication = 2
        elif sys['Authentication'] == 'Externally Managed':
            it.authentication = 3

        if sys['Access'] == 'Public Internet':
            it.access = 1
        elif sys['Access'] == 'Internet accessible':
            it.access = 1
        elif sys['Access'] == 'Corporate Network':
            it.access = 3
        elif sys['Access'] == 'Local System (Networked)':
            it.access = 4

        it.description = sys['Description']

        if sys['Criticality'] == 'Critical':
            it.criticality = 1
        elif sys['Criticality'] == 'Moderate':
            it.criticality = 2
        elif sys['Criticality'] == 'Low':
            it.criticality = 3

        if sys['Availability'] == '24/7/365':
            it.availability = 1
        else:
            it.availability = 2

        it.notes = sys['Notes']
        it.link = sys['Link']

        if sys['Owner']:
            names = sys['Owner'].split()
            given_name, surname = names[0], names[1]
            if DepartmentUser.objects.filter(given_name=given_name, surname=surname).exists():
                it.owner = DepartmentUser.objects.get(given_name=given_name, surname=surname)
        if sys['Custodian']:
            names = sys['Custodian'].split()
            given_name, surname = names[0], names[1]
            if DepartmentUser.objects.filter(given_name=given_name, surname=surname).exists():
                it.custodian = DepartmentUser.objects.get(given_name=given_name, surname=surname)
        if sys['Data custodian']:
            names = sys['Data custodian'].split()
            given_name, surname = names[0], names[1]
            if DepartmentUser.objects.filter(given_name=given_name, surname=surname).exists():
                it.data_custodian = DepartmentUser.objects.get(given_name=given_name, surname=surname)

        # Finally, save the whole CSV in extra_data
        it.extra_data = json.dumps(sys)

        it.save()
        print('Saved {}'.format(it))
