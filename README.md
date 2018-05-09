OIM Extranet
============

This project contains the CMS to provide the OIM Extranet site, which is
based upon the [Wagtail CMS](https://wagtail.io/).

Installation
------------

Install required libraries using `pip`:

    pip install -r requirements.txt

Development
-----------

This project uses confy to set environment variables (in a `.env` file).
For local development, minimum required settings are as follows:

    DEBUG=True
    DATABASE_URL="postgis://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
    SECRET_KEY="ThisIsASecretKey"
    BASE_URL="HOST<:PORT>"
    ALLOWED_DOMAINS=".dbca.wa.gov.au"
