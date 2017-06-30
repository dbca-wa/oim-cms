[![Build
status](https://travis-ci.org/parksandwildlife/oim-cms.svg?branch=master)](https://travis-ci.org/parksandwildlife/oim-cms/builds) [![Coverage Status](https://coveralls.io/repos/github/parksandwildlife/oim-cms/badge.svg?branch=master)](https://coveralls.io/github/parksandwildlife/oim-cms?branch=master)

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

    DEBUG=True
    DATABASE_URL="postgis://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
    SECRET_KEY="ThisIsASecretKey"
    BASE_URL="HOST:PORT"
    FRESHDESK_ENDPOINT="https://dpaw.freshdesk.com/api/v2"
    FRESHDESK_KEY="SecretAPIKeyValue"
    PDQ_INV_PATH="/path/to/pdq_inventory/mount"
    AZUREAD_AUTHORITY="https://login.microsoftonline.com/thisisnotarealazureaudauthorityurl"
