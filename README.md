OIM Extranet
============

This project contains the CMS to provide the OIM Extranet site, which is
based upon the [Wagtail CMS](https://wagtail.io/).

Installation
------------

Install required libraries using `pip`:

    pip install -r requirements.txt

Notes
-----

This project is focused on Parks and Wildlife use cases at this point in time,
for more information please contact asi@dpaw.wa.gov.au.

Development
-----------

This project uses confy to set environment variables (in a `.env` file).
For local development, minimum required settings are as follows:

    DJANGO_SETTINGS_MODULE="oim_cms.settings"
    DEBUG=True
    DATABASE_URL="postgis://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
    SECRET_KEY="ThisIsASecretKey"
    BASE_URL="HOST:PORT"
    FRESHDESK_ENDPOINT="https://dpaw.freshdesk.com/api/v2"
    FRESHDESK_KEY="SecretAPIKeyValue"
    PDQ_INV_PATH="/path/to/pdq_inventory/mount"
