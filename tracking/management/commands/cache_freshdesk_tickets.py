from django.core.management.base import BaseCommand
import json
import requests
from time import sleep
from tracking import utils_freshdesk
from tracking.utils import logger_setup


class Command(BaseCommand):
    help = 'Download and cache Freshdesk tickets.'

    def add_arguments(self, parser):
        # Named (optional) arguments:
        parser.add_argument(
            '-l',
            '--limit',
            action='store',
            dest='limit',
            default=0,  # No limit.
            type=int,
            help='Maximum number of tickets to download and cache.',
        )

    def handle(self, *args, **options):
        logger = logger_setup('freshdesk_cache_all_tickets')
        logger_headers = logger_setup('freshdesk_api_response_headers')
        # Begin by caching Agents as Contacts.
        print('Caching Freshdesk Agents as Contacts')
        logger.info('Caching Freshdesk Agents as Contacts')
        utils_freshdesk.freshdesk_cache_agents()
        # Next, start caching tickets one page at a time.
        url = utils_freshdesk.FRESHDESK_ENDPOINT + '/tickets'
        params = {'page': 1, 'per_page': 100}
        further_results = True
        cached_count = 0

        while further_results:
            if options['limit'] and (cached_count + params['per_page']) >= options['limit']:
                params['per_page'] = options['limit'] - cached_count
            print('Retrieving Freshdesk tickets page {}'.format(params['page']))
            logger.info('Retrieving Freshdesk tickets page {}'.format(params['page']))
            r = requests.get(url, auth=utils_freshdesk.FRESHDESK_AUTH, params=params)
            logger_headers.info(json.dumps(dict(r.headers)))
            # If we've been rate-limited, response status will be 429.
            # Sleep for the number of seconds specifief by the Retry-After header.
            if r.status_code == 429:
                if 'retry-after' in r.headers:
                    naptime = r.headers['retry-after']
                else:
                    naptime = 3600  # Sleep for an hour.
                print('HTTP 429 receiving, sleeping {} seconds'.format(naptime))
                logger.warning('HTTP 429 receiving, sleeping {} seconds'.format(naptime))
                sleep(naptime)
            # If the response
            elif r.status_code == 200:
                if 'link' not in r.headers:  # No further paginated results.
                    print('No further pages of results')
                    logger.info('No further pages of results')
                    further_results = False
                else:
                    params['page'] += 1
                tickets = r.json()
                print('Caching {} tickets'.format(len(tickets)))
                logger.info('Caching {} tickets'.format(len(tickets)))
                cache = utils_freshdesk.freshdesk_cache_tickets(tickets)
                if not cache:  # Error!
                    print('Exception in freshdesk_cache_tickets; check log')
                    logger.error('Exception in freshdesk_cache_tickets; check log')
                    further_results = False
                cached_count += len(tickets)
                if options['limit'] and cached_count >= options['limit']:
                    print('Caching limit reached; terminating.')
                    further_results = False
            else:
                print('Tickets API response was neither 200 or 429, aborting')
                logger.error('Tickets API response was neither 200 or 429, aborting')
                further_results = False
