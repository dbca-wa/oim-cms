from django.conf import settings
from django.core.mail import send_mail
import json
import os
import requests
import socket
from tracking.models import DepartmentUser
from tracking.utils import logger_setup


FRESHDESK_ENDPOINT = os.environ['FRESHDESK_ENDPOINT']
FRESHDESK_AUTH = (os.environ['FRESHDESK_KEY'], 'X')
HEADERS_JSON = {'Content-Type': 'application/json'}


def get_freshdesk_user(fd_id):
    """Query the Freshdesk API for a single user's details.
    """
    # Query customers
    url = FRESHDESK_ENDPOINT + '/contacts/{}.json'.format(fd_id)
    resp = requests.get(url, auth=FRESHDESK_AUTH, headers=HEADERS_JSON)
    return resp.json()


def get_freshdesk_companies(progress=True):
    """Utility function to harvest all companies (customers) via the Freshdesk
    API. Returns a dict of dicts.
    """
    url = FRESHDESK_ENDPOINT + '/customers.json'
    data = {'page': 1}
    customers = []
    api_resp = True

    while api_resp:
        if progress:
            print('Querying page {}'.format(data['page']))

        resp = requests.get(
            url, auth=FRESHDESK_AUTH, data=json.dumps(data), headers=HEADERS_JSON)
        if not resp.status_code == 200:
            resp.raise_for_status()

        j = resp.json()
        if not j:  # Empty response from the API.
            api_resp = False
            if progress:
                print('Done!')

        customers.extend(j)
        data['page'] += 1

    # Turn customers into a dict of dicts, using name as key.
    customers = {c['customer']['name']: c['customer'] for c in customers}
    return customers


def get_freshdesk_users(progress=True):
    """Utility function to harvest all users via the Freshdesk API.
    Note that the function may take a significant amount of time to return a
    value, depending on the number of customers. NOTE: does not return Agents.
    Returns a dict of dicts (email as key).
    """
    # Query customers
    url = FRESHDESK_ENDPOINT + '/contacts.json'
    data = {'page': 1}
    api_resp = True
    contacts = []

    while api_resp:
        if progress:
            print('Querying page {}'.format(data['page']))

        resp = requests.get(
            url, auth=FRESHDESK_AUTH, data=json.dumps(data), headers=HEADERS_JSON)
        if not resp.status_code == 200:
            resp.raise_for_status()

        j = resp.json()
        if not j:  # Empty response from the API.
            api_resp = False
            if progress:
                print('Done querying customers')
        else:
            contacts.extend(j)
            data['page'] += 1  # Next page of contacts

    # Turn contacts into a dict of dicts, using email as key.
    users = {c['user']['email'].lower(): c['user'] for c in contacts if c['user']['email']}

    return users


def get_freshdesk_agents(progress=True):
    """Utility function to harvest all agents via the Freshdesk API.
    Returns a dict of dicts (email as key).
    """
    # FIXME: the Freshdesk API does not allow updates to users that are agents.
    # Query agents.
    url = FRESHDESK_ENDPOINT + '/agents.json'
    data = {'page': 1}
    api_resp = True
    agents = []

    while api_resp:
        if progress:
            print('Querying page {}'.format(data['page']))

        resp = requests.get(url, auth=FRESHDESK_AUTH, data=json.dumps(data), headers=HEADERS_JSON)
        if not resp.status_code == 200:
            resp.raise_for_status()

        j = resp.json()
        if not j:  # Empty response from the API.
            api_resp = False
            if progress:
                print('Done querying agents')
        else:
            agents.extend(j)
            data['page'] += 1  # Next page of agents

    # Turn agents into a dict of dicts, using email as key.
    agents = {a['agent']['user']['email'].lower(): a['agent']['user'] for a in agents if a['agent']['user']['email']}

    return agents


def freshdesk_contact_create(data):
    """Function to create a new Freshdesk contact. Accepts a dict of fields
    See: http://freshdesk.com/api#create_user
    """
    url = FRESHDESK_ENDPOINT + '/contacts.json'
    data = {'user': data}
    resp = requests.post(
        url, auth=FRESHDESK_AUTH, data=json.dumps(data), headers=HEADERS_JSON)

    return resp


def freshdesk_contact_update(id, data):
    """Function to update a Freshdesk contact. Accepts an ID and dict of fields.
    See: http://freshdesk.com/api#update_user
    """
    url = FRESHDESK_ENDPOINT + '/contacts/{}.json'.format(id)
    data = {'user': data}
    resp = requests.put(
        url, auth=FRESHDESK_AUTH, data=json.dumps(data), headers=HEADERS_JSON)

    return resp


def freshdesk_sync_contacts(contacts=None, companies=None, agents=None):
    """Iterate through all DepartmentUser objects, and ensure that each user's
    information is synced correctly to a Freshdesk contact.
    May optionally be passed in dicts of contacts & companies.
    """
    logger = logger_setup('freshdesk_sync_contacts')

    try:
        if not contacts:
            logger.info('Querying Freshdesk for current contacts')
            contacts = get_freshdesk_users(progress=True)
        if not companies:
            logger.info('Querying Freshdesk for current companies')
            companies = get_freshdesk_companies(progress=False)
        if not agents:
            logger.info('Querying Freshdesk for current agents')
            agents = get_freshdesk_agents(progress=False)
    except Exception as e:
        send_mail(
            'Freshdesk "all contacts" API query failed: {}'.format(socket.gethostname()),
            '''Freshdesk "all contacts" query failed for host {}, '''
            '''project directory {}\nException:\n{}'''.format(
                socket.gethostname(), os.path.dirname(__file__), e),
            'incredibus@dpaw.wa.gov.au',
            list(settings.ADMINS),
            fail_silently=False)
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

            if (user.name != fd['name'] or user.telephone != fd['phone'] or user.title != fd['job_title']):
                user_sync = True
                data['name'] = user.name
                data['phone'] = user.telephone
                data['job_title'] = user.title
            if department and department in companies and fd['company_id'] != companies[department]['id']:
                user_sync = True
                data['company_id'] = companies[department]['id']
            # Custom fields in Freshdesk: Cost Centre no.
            if fd['custom_field']['cf_cost_centre'] != cost_centre:
                user_sync = True
                data['custom_field'] = {'cf_cost_centre': cost_centre}
            # Custom fields in Freshdesk: Physical location
            if fd['custom_field']['cf_location'] != physical_location:
                user_sync = True
                if 'custom_field' in data:
                    data['custom_field']['cf_location'] = physical_location
                else:
                    data['custom_field'] = {'cf_location': physical_location}
            if user_sync:  # Sync user details to their Freshdesk contact.
                resp = freshdesk_contact_update(fd['id'], data)
                if resp.status_code == 403:  # Forbidden
                    # A 403 response probably means that we hit the API throttle limit.
                    # Abort the synchronisation.
                    logger.error('HTTP403 received from Freshdesk API, aborting')
                    return False
                logger.info('{} was updated in Freshdesk (status {})'.format(user.email.lower(), resp.status_code))
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
            resp = freshdesk_contact_create(data)
            if not resp.status_code == 200:  # Error, unable to process request.
                logger.warn('{} not created in Freshdesk (status {})'.format(user.email.lower(), resp.status_code))
            else:
                logger.info('{} created in Freshdesk (status {})'.format(user.email.lower(), resp.status_code))

    return True
