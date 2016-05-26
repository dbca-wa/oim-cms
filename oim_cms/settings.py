import os
from confy import env, database, cache

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

# Define the following in the environment:
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG', False)
ALLOWED_HOSTS = [env("ALLOWED_DOMAIN"), ]
INTERNAL_IPS = ['127.0.0.1', '::1']

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
BASE_URL = env('BASE_URL', 'http://localhost:8000')
BORG_URL = env("BORG_URL", "https://borg.dpaw.wa.gov.au")
if BORG_URL.endswith("/"):
    BORG_URL = BORG_URL[:-1]

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    #
    'django.contrib.gis',

    'compressor',
    'taggit',
    'modelcluster',
    'django_extensions',
    'reversion',
    'mptt',
    'leaflet',

    'wagtail.wagtailcore',
    'wagtail.wagtailadmin',
    'wagtail.wagtaildocs',
    'wagtail.wagtailsnippets',
    'wagtail.wagtailusers',
    'wagtail.wagtailsites',
    'wagtail.wagtailimages',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsearch',
    'wagtail.wagtailredirects',
    'wagtail.wagtailforms',
    'django_uwsgi',

    'social.apps.django_app.default',

    'tracking',
    'registers',
    'core',
    'mudmap',
    'postgrest',
    #'catalogue',
    'rooms'
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social.backends.azuread.AzureADOAuth2',
)
LDAP_SERVER_URI = env('LDAP_SERVER_URI', 'ldap://')
LDAP_ACCESS_DN = env('LDAP_ACCESS_DN', 'dn')
LDAP_ACCESS_PASSWORD = env('LDAP_ACCESS_PASSWORD', 'pass')
LDAP_SEARCH_SCOPE = env('LDAP_SEARCH_SCOPE', 'scope')
import ldap
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion, GroupOfNamesType
# LDAP settings.
AUTH_LDAP_SERVER_URI = LDAP_SERVER_URI
AUTH_LDAP_BIND_DN = LDAP_ACCESS_DN
AUTH_LDAP_BIND_PASSWORD = LDAP_ACCESS_PASSWORD
AUTH_LDAP_ALWAYS_UPDATE_USER = False
AUTH_LDAP_AUTHORIZE_ALL_USERS = True
AUTH_LDAP_FIND_GROUP_PERMS = False
AUTH_LDAP_MIRROR_GROUPS = False
AUTH_LDAP_CACHE_GROUPS = False
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 300
AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
    LDAPSearch('{}'.format(LDAP_SEARCH_SCOPE),
               ldap.SCOPE_SUBTREE,
               '(sAMAccountName=%(user)s)'),
    LDAPSearch('{}'.format(LDAP_SEARCH_SCOPE),
               ldap.SCOPE_SUBTREE,
               '(mail=%(user)s)'),
)
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    '{}'.format(LDAP_SEARCH_SCOPE),
    ldap.SCOPE_SUBTREE, '(objectClass=group)'
)
AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: False,
    ldap.OPT_REFERRALS: False,
}
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr='cn')
AUTH_LDAP_USER_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}
SOCIAL_AUTH_AZUREAD_OAUTH2_KEY = env('AZUREAD_CLIENTID', 'clientid')
SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET = env('AZUREAD_SECRETKEY', 'secret')
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_TRAILING_SLASH = False
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/"
SOCIAL_AUTH_PIPELINE = (
    'social.pipeline.social_auth.social_details',
    'social.pipeline.social_auth.social_uid',
    'social.pipeline.social_auth.auth_allowed',
    'social.pipeline.social_auth.social_user',
    'social.pipeline.user.get_username',
    'social.pipeline.social_auth.associate_by_email',
    'social.pipeline.user.create_user',
    'social.pipeline.social_auth.associate_user',
    'social.pipeline.social_auth.load_extra_data',
    'social.pipeline.user.user_details',
)
SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN', None)
if env('SESSION_COOKIE_NAME', None):
    SESSION_COOKIE_NAME = env('SESSION_COOKIE_NAME', None)
else:
    if SESSION_COOKIE_DOMAIN:
        SESSION_COOKIE_NAME = (SESSION_COOKIE_DOMAIN + ".sessionid").replace(".", "_")
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_HTTPONLY = env('SESSION_COOKIE_HTTPONLY', False)
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', False)
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', False)

CACHES = {'default': cache.config()}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',

    'dpaw_utils.middleware.SSOLoginMiddleware',
)

ROOT_URLCONF = 'oim_cms.urls'
WSGI_APPLICATION = 'oim_cms.wsgi.application'


DATABASES = {'default': database.config()}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Australia/Perth'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = 'd M Y'
DATETIME_FORMAT = 'l d F Y, h:i A'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATIC_URL = '/static/'
COMPRESS_ENABLED = False

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
                # Insert your TEMPLATE_CONTEXT_PROCESSORS above here
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Pusher settings
PUSHER_APP_ID = env('PUSHER_APP_ID', None)
PUSHER_KEY = env('PUSHER_KEY', None)
PUSHER_SECRET = env('PUSHER_SECRET', None)
PUSHER_CLUSTER=env('PUSHER_CLUSTER', None)
# Incredibus settings
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Define the following in .env
DOMAIN_SUFFIX = env('DOMAIN_SUFFIX', None)
API_SECRET = env('API_SECRET', None)
AD_FILTER_COMPUTERS = env('AD_FILTER_COMPUTERS', None)
AD_FILTER_SOFTWARE = env('AD_FILTER_SOFTWARE', None)
AD_FILTER_PUBLISHERS = env('AD_FILTER_PUBLISHERS', None)
AD_FILTER_USERS = env('AD_FILTER_USERS', None)
EXCH_REPORT_PATH = env('EXCH_REPORT_PATH', None)
NETWORK_SCAN_PATH = env('NETWORK_SCAN_PATH', None)
DNS_PATH = env('DNS_PATH', None)
PDQ_INV_PATH = env('PDQ_INV_PATH', None)
PDQ_DHCP_PATH = env('PDQ_DHCP_PATH', None)
PEEPERS_URL = env('PEEPERS_URL', None)
INTERNAL_USER = env('INTERNAL_USER', None)
FRESHDESK_ENDPOINT = env('FRESHDESK_ENDPOINT', None)
FRESHDESK_AUTH = (env('FRESHDESK_KEY'), 'X')
POSTGREST_ROLE = env('POSTGREST_ROLE', 'postgrest')
POSTGREST_BINARY = env('POSTGREST_BINARY', '/usr/local/bin/postgrest')

# Email settings
EMAIL_HOST = env('EMAIL_HOST', None)
EMAIL_PORT = env('EMAIL_PORT', None)
EMAIL_INCREDIBUS_LIST = env('EMAIL_INCREDIBUS_LIST', '')
if not EMAIL_INCREDIBUS_LIST:
    EMAIL_INCREDIBUS_LIST = []
else:
    EMAIL_INCREDIBUS_LIST = EMAIL_INCREDIBUS_LIST.split(',')

# Wagtail settings

WAGTAIL_SITE_NAME = "OIM Content Management System"

# Use Elasticsearch as the search backend for extra performance and better search results:
# http://wagtail.readthedocs.org/en/latest/howto/performance.html#search
# http://wagtail.readthedocs.org/en/latest/core_components/search/backends.html#elasticsearch-backend
#
# WAGTAILSEARCH_BACKENDS = {
#     'default': {
#         'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
#         'INDEX': 'oim_cms',
#     },
# }


# Whether to use face/feature detection to improve image cropping - requires OpenCV
WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = False

# enable image usage stats in the admin
WAGTAIL_USAGE_COUNT_ENABLED = True

# we want a custom search result template
WAGTAILSEARCH_RESULTS_TEMPLATE = 'core/search_results.html'

# Logging settings
# Ensure that the logs directory exists:
if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.mkdir(os.path.join(BASE_DIR, 'logs'))
LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'cms.log'),
            'formatter': 'verbose',
            'maxBytes': '5242880'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'INFO'
        },
        'log': {
            'handlers': ['file'],
            'level': 'INFO'
        },
    }
}
if DEBUG:
    # Developer local IP may be required for debug_toolbar to work/
    if env('INTERNAL_IP', False):
        INTERNAL_IPS.append(env('INTERNAL_IP'))
    INSTALLED_APPS += (
        'debug_toolbar',
    )
    DEBUG_TOOLBAR_PATCH_SETTINGS = True
    MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE_CLASSES
