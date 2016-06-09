import os
import requests
from tracking.models import DepartmentUser
from tracking.utils import logger_setup


FRESHDESK_ENDPOINT = os.environ['FRESHDESK_ENDPOINT']
FRESHDESK_AUTH = (os.environ['FRESHDESK_KEY'], 'X')
HEADERS_JSON = {'Content-Type': 'application/json'}


def get_freshdesk_contact(cid):
    """Query the Freshdesk v2 API for a single contact's details.
    """
    url = FRESHDESK_ENDPOINT + '/contacts/{}'.format(cid)
    r = requests.get(url, auth=FRESHDESK_AUTH)
    if not r.status_code == 200:
        r.raise_for_status()
    return r.json()


def update_freshdesk_contact(data, create=True, cid=None):
    """Use the Freshdesk v2 API to create or update a contact.
    Accepts a dict of fields.
    Ref: https://developer.freshdesk.com/api/#create_contact
    """
    if not cid:
        url = FRESHDESK_ENDPOINT + '/contacts'
    else:
        url = FRESHDESK_ENDPOINT + '/contacts/{}'.format(cid)
    if create:
        resp = requests.post(url, auth=FRESHDESK_AUTH, data=data)
    else:
        resp = requests.put(url, auth=FRESHDESK_AUTH, data=data)

    return resp


def get_freshdesk_objects(obj_type, progress=True):
    """Query the Freshdesk v2 API for all objects of a defined type.
    May take some time, depending on the number of objects.
    """
    url = FRESHDESK_ENDPOINT + '/{}'.format(obj_type)
    params = {'page': 1, 'per_page': 100}
    objects = []
    further_results = True

    while further_results:
        if progress:
            print('Querying page {}'.format(params['page']))

        r = requests.get(url, auth=FRESHDESK_AUTH, params=params)
        if not r.status_code == 200:
            r.raise_for_status()

        if 'link' not in r.headers:  # No further paginated results.
            further_results = False
            if progress:
                print('Done!')

        objects.extend(r.json())
        params['page'] += 1
    # Return the full list of objects returned.
    return objects


def freshdesk_sync_contacts(contacts=None, companies=None, agents=None):
    """Iterate through all DepartmentUser objects, and ensure that each user's
    information is synced correctly to a Freshdesk contact.
    May optionally be passed in dicts of contacts & companies.
    """
    logger = logger_setup('freshdesk_sync_contacts')

    try:
        if not contacts:
            logger.info('Querying Freshdesk for current contacts')
            contacts = get_freshdesk_objects(obj_type='contacts', progress=True)
            contacts = {c['email'].lower(): c for c in contacts if c['email']}
        if not companies:
            logger.info('Querying Freshdesk for current companies')
            companies = get_freshdesk_objects(obj_type='companies', progress=False)
            companies = {c['name']: c for c in companies}
        if not agents:
            logger.info('Querying Freshdesk for current agents')
            agents = get_freshdesk_objects(obj_type='agents', progress=False)
            agents = {a['contact']['email'].lower(): a['contact'] for a in agents if a['contact']['email']}
    except Exception as e:
        logger.exception(e)
        return False

    # Filter DepartmentUsers: valid email (contains @), not -admin, DN contains 'OU=Users'
    for user in DepartmentUser.objects.filter(email__contains='@', ad_dn__contains='OU=Users').exclude(email__contains='-admin'):
        if user.email.lower() in contacts:
            # The DepartmentUser exists in Freshdesk; verify and update details.
            fd = contacts[user.email.lower()]
            data = {}
            user_sync = False
            # use extra attributes from org_data, if available
            cost_centre = user.org_data.get('cost_centre', {}).get('code', "") if user.org_data else ""
            physical_location = user.org_data.get('location', {}).get('name', "") if user.org_data else ""
            department = user.org_data.get('units', []) if user.org_data else []
            department = department[0].get('name', "") if len(department) > 0 else ""
            changes = []

            if user.name != fd['name']:
                user_sync = True
                data['name'] = user.name
                changes.append('name')
            if user.telephone != fd['phone']:
                user_sync = True
                data['phone'] = user.telephone
                changes.append('phone')
            if user.title != fd['job_title']:
                user_sync = True
                data['job_title'] = user.title
                changes.append('job_title')
            if department and department in companies and fd['company_id'] != companies[department]['id']:
                user_sync = True
                data['company_id'] = companies[department]['id']
                changes.append('company_id')
            # Custom fields in Freshdesk: Cost Centre no.
            if fd['custom_field']['cf_cost_centre'] != cost_centre:
                user_sync = True
                data['custom_field'] = {'cf_cost_centre': cost_centre}
                changes.append('cost_centre')
            # Custom fields in Freshdesk: Physical location
            if fd['custom_field']['cf_location'] != physical_location:
                user_sync = True
                if 'custom_field' in data:
                    data['custom_field']['cf_location'] = physical_location
                else:
                    data['custom_field'] = {'cf_location': physical_location}
                changes.append('physical_location')
            if user_sync:  # Sync user details to their Freshdesk contact.
                resp = update_freshdesk_contact(data, create=False, cid=fd['id'])  # Update the contact.
                if resp.status_code == 403:  # Forbidden
                    # A 403 response probably means that we hit the API throttle limit.
                    # Abort the synchronisation.
                    logger.error('HTTP403 received from Freshdesk API, aborting')
                    return False
                logger.info('{} was updated in Freshdesk (status {}), changed: {}'.format(
                    user.email.lower(), resp.status_code, ', '.join(changes)))
            else:
                logger.info('{} already up to date in Freshdesk'.format(user.email.lower()))
        elif user.email.lower() in agents:
            # The DepartmentUser is an agent; skip (can't update Agent details via the API).
            logger.info('{} is an agent, skipping sync'.format(user.email.lower()))
            continue
        else:
            # The DepartmentUser does not exist in Freshdesk; create them as a Contact.
            data = {'name': user.name, 'email': user.email.lower(),
                    'phone': user.telephone, 'job_title': user.title}
            if department and department in companies:
                data['company_id'] = companies[department]['id']
            resp = update_freshdesk_contact(data)  # Create the contact.
            if not resp.status_code == 200:  # Error, unable to process request.
                logger.warn('{} not created in Freshdesk (status {})'.format(user.email.lower(), resp.status_code))
            else:
                logger.info('{} created in Freshdesk (status {})'.format(user.email.lower(), resp.status_code))

    return True
