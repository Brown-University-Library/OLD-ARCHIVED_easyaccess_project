# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json, logging, os
import dj_database_url


## ============================================================================
## standard project-level settings
## ============================================================================

BASE_DIR = os.path.dirname( os.path.dirname(os.path.abspath(__file__)) )  # does not include trailing slash
# print( 'BASE_DIR, ```%s```' % BASE_DIR )

SECRET_KEY = os.environ['EZACS__SECRET_KEY']

DEBUG = json.loads( os.environ['EZACS__DEBUG_JSON'] )  # will be True or False
DEBUG2 = json.loads( os.environ['EZACS__DEBUG2_JSON'] )  # will be True or False

# TEMPLATE_DEBUG = DEBUG

ADMINS = json.loads( os.environ['EZACS__ADMINS_JSON'] )
MANAGERS = ADMINS

SITE_ID = 1

DATABASES = json.loads( os.environ['EZACS__DATABASES_JSON'] )

TIME_ZONE = 'America/New_York'

USE_TZ = False

## https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = os.environ['EZACS__STATIC_URL']
STATIC_ROOT = os.environ['EZACS__STATIC_ROOT']  # needed for collectstatic command

APPEND_SLASH = True

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )

ROOT_URLCONF = 'config.urls'

# AUTH_PROFILE_MODULE = 'delivery.LibraryProfile'  # <http://deathofagremmie.com/2014/05/24/retiring-get-profile-and-auth-profile-module/>

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bul_link',
    'findit',
    'delivery',
    'django.contrib.admin',
    'shorturls',
    'article_request_app'
    )

SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.environ['EZACS__CACHE_LOCATION'],
    }
}

SERVER_EMAIL = os.environ['EZACS__SERVER_EMAIL']
EMAIL_HOST = os.environ['EZACS__EMAIL_HOST']
EMAIL_PORT = int( os.environ['EZACS__EMAIL_PORT'] )

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

## logging
"""
See http://stackoverflow.com/questions/1598823/elegant-setup-of-python-logging-in-django
Note: if disable_existing_loggers is False, result is lots of logging output from imported modules.
Note: to see the imported modules' loggers, add somewhere:
    import logging
    existing_logger_names = logging.getLogger().manager.loggerDict.keys()
    print '- EXISTING_LOGGER_NAMES, `%s`' % existing_logger_names
    (from <https://bytes.com/topic/python/answers/830042-dynamically-getting-loggers>)

    Running the above lines from findit/tests/test_views.py, I get...
    [19/Apr/2019 10:10:15] DEBUG [test_views-<module>()::16] logging ready
    - EXISTING_LOGGER_NAMES, `['bs4', 'urllib3.poolmanager', 'easyaccess_project.findit.tests', 'illiad.account', 'django.db.backends.schema', 'django.request', 'django.template', 'django.server', 'findit.classes', 'illiad', 'urllib3.connection', 'bibjsontools', 'access', 'django.security.csrf', 'urllib3.response', 'urllib3.util', 'django.db', 'django.db.backends', 'easyaccess_project', 'py360link2.link360', 'findit.classes.view_info_helper', 'link360', 'urllib3', 'findit', 'beautifulsoup4', 'easyaccess_project.findit.tests.test_views', 'easyaccess_project.findit', 'urllib3.util.retry', 'django.security', 'django', 'requests', 'urllib3.connectionpool', 'py360link2']`
"""

# import logging
# existing_logger_names = logging.getLogger().manager.loggerDict.keys()
# print( '- EXISTING_LOGGER_NAMES, `%s`' % existing_logger_names )

## disabling module loggers
logging.getLogger('beautifulsoup4').setLevel( logging.WARNING )
logging.getLogger('bibjsontools').setLevel( logging.WARNING )
logging.getLogger('bs4').setLevel( logging.WARNING )
logging.getLogger('illiad').setLevel( logging.WARNING )
logging.getLogger('illiad.account').setLevel( logging.WARNING )
logging.getLogger('link360').setLevel( logging.WARNING )
logging.getLogger('py360link2').setLevel( logging.WARNING )
logging.getLogger('requests').setLevel( logging.WARNING )
logging.getLogger('urllib3').setLevel( logging.WARNING )
logging.getLogger('urllib3.connection').setLevel( logging.WARNING )
logging.getLogger('urllib3.connectionpool').setLevel( logging.WARNING )
logging.getLogger('urllib3.poolmanager').setLevel( logging.WARNING )
logging.getLogger('urllib3.response').setLevel( logging.WARNING )
logging.getLogger('urllib3.util').setLevel( logging.WARNING )
logging.getLogger('urllib3.util.retry').setLevel( logging.WARNING )


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        # 'null': {
        #     'level':'DEBUG',
        #     'class':'django.utils.log.NullHandler',
        # },
        # 'console':{
        #     'level': 'DEBUG',
        #     'class': 'logging.StreamHandler',
        #     'formatter': 'simple'
        # },
        'illiad_log_file':{
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.environ['EZACS__ILLIAD_LOG_FILE'],
            'formatter': 'verbose'
        },
        'access_log_file':{
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.environ['EZACS__ACCESS_LOG_FILE'],
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': json.loads( os.environ['EZACS__LOG_PROPAGATE_LEVEL_JSON'] ),
            },
        'illiad': {
            'handlers': ['illiad_log_file'],
            'level': os.environ['EZACS__ILLIAD_LOG_LEVEL'],
            'propagate': json.loads( os.environ['EZACS__LOG_PROPAGATE_LEVEL_JSON'] ),
            },
        'access': {
            'handlers': ['access_log_file'],
            'level': os.environ['EZACS__ACCESS_LOG_LEVEL'],
            'propagate': json.loads( os.environ['EZACS__LOG_PROPAGATE_LEVEL_JSON'] ),
            },
        }
    }

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    )

# TEMPLATE_CONTEXT_PROCESSORS = (
#     'django.contrib.auth.context_processors.auth',
#     'django.core.context_processors.debug',
#     'django.core.context_processors.i18n',
#     'django.core.context_processors.media',
#     'django.core.context_processors.static',
#     'django.contrib.auth.context_processors.auth',
#     'django.contrib.messages.context_processors.messages',
#     )

# template_dirs = json.loads( os.environ['EZACS__TEMPLATE_DIRS_JSON'] )  # list
# template_dirs = [
#     '%s/findit' % BASE_DIR,
#     '%s/delivery' % BASE_DIR,
#     '%s/article_request_app' % BASE_DIR
#     ]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            '%s/findit' % BASE_DIR,
            '%s/delivery' % BASE_DIR,
            '%s/article_request_app' % BASE_DIR
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGIN_URL = os.environ['EZACS__LOGIN_URL']
LOGIN_REDIRECT_URL = os.environ['EZACS__LOGIN_REDIRECT_URL']

ALLOWED_HOSTS = json.loads( os.environ['EZACS__ALLOWED_HOSTS_JSON'] )

CSRF_TRUSTED_ORIGINS = json.loads( os.environ['EZACS__CSRF_TRUSTED_ORIGINS_JSON'] )

## end of project-level settings


## ============================================================================
## findit app settings
## ============================================================================

BUL_LINK_SERSOL_KEY = os.environ['EZACS__BUL_LINK_SERSOL_KEY']
BUL_LINK_CACHE_TIMEOUT = int( os.environ['EZACS__BUL_LINK_CACHE_TIMEOUT'] ) * ( (60 * 60) * 24 )  # days, converted to required seconds
BUL_LINK_PERMALINK_PREFIX = os.environ['EZACS__BUL_LINK_PERMALINK_PREFIX']
BUL_LINK_SERSOL_TIMEOUT = int( os.environ['EZACS__BUL_LINK_SERSOL_TIMEOUT'] )  # seconds to wait for hitting the sersol api

FINDIT_PERMALINK_PREFIX = os.environ['EZACS__FINDIT_PERMALINK_PREFIX']
FINDIT_PRINT_PROVIDER = os.environ['EZACS__FINDIT_PRINT_PROVIDER']

FINDIT_BOOK_RESOLVER = os.environ['EZACS__FINDIT_BOOK_RESOLVER']

FINDIT_ILLIAD_URL = os.environ['EZACS__FINDIT_ILLIAD_URL']
FINDIT_ILLIAD_KEY = os.environ['EZACS__FINDIT_ILLIAD_KEY']
FINDIT_ILLIAD_REMOTE_AUTH_URL = os.environ['EZACS__FINDIT_ILLIAD_REMOTE_AUTH_URL']
FINDIT_ILLIAD_REMOTE_AUTH_HEADER = os.environ['EZACS__FINDIT_ILLIAD_REMOTE_AUTH_HEADER']
FINDIT_EMAIL_FROM = os.environ['EZACS__FINDIT_EMAIL_FROM']

FINDIT_MENDELEY_CONSUMER_KEY = os.environ['EZACS__FINDIT_MENDELEY_CONSUMER_KEY']
FINDIT_MENDELEY_SECRET_KEY = os.environ['EZACS__FINDIT_MENDELEY_SECRET_KEY']

FINDIT_MAS_KEY = os.environ['EZACS__FINDIT_MAS_KEY']  # microsoft academic search?

FINDIT_STAFF_USERS = json.loads( os.environ['EZACS__FINDIT_STAFF_USERS_JSON'] )  # list; these will be given staff status for the admin app

FINDIT_SUMMON_ID = os.environ['EZACS__FINDIT_SUMMON_ID']
FINDIT_SUMMON_KEY = os.environ['EZACS__FINDIT_SUMMON_KEY']

FINDIT_SERVICE_ACTIVE = True  # notes said "Turn on or off." -- why would this ever be off?

FINDIT_DB_SORT_BY = [
    'American Association for the Advancement of Science',
    'Nature Publishing',
    'Massachusetts Medical Society',
    'American Medical Association',
    'Ovid',
    'Project MUSE',
    'JSTOR',
    'Wiley-Blackwell',
    'Elsevier',
    ]
FINDIT_DB_PUSH_TOP = []
FINDIT_DB_PUSH_BOTTOM = ['EBSCOhost', 'LexisNexis', 'EBSCO Discovery Service']

FINDIT_GSCHOLAR = os.environ['EZACS__FINDIT_GSCHOLAR']

FINDIT_SKIP_SUMMON_DIRECT_LINK = ['summon', 'worldcat', 'pubmed']  # list of referring sites to not consult Summon for.

FINDIT_SHIB_FRAGMENT = unicode( os.environ['EZACS__FINDIT_SHIB_FRAGMENT'] )


# ===============================================================================
# common settings -- used different places
# ===============================================================================

SHIB_AFFILIATION_KEY = unicode( os.environ['EZACS__COMMON_SHIB_AFFILIATION_KEY'] )
SHIB_AFFILIATIONPRIMARY_KEY = unicode( os.environ['EZACS__COMMON_SHIB_AFFILIATIONPRIMARY_KEY'] )
SHIB_AFFILIATIONSCOPED_KEY = unicode( os.environ['EZACS__COMMON_SHIB_AFFILIATIONSCOPED_KEY'] )
SHIB_BARCODE_KEY = unicode( os.environ['EZACS__COMMON_SHIB_BARCODE_KEY'] )
SHIB_DEPARTMENT_KEY = unicode( os.environ['EZACS__COMMON_SHIB_DEPARTMENT_KEY'] )
SHIB_ENTITLEMENT_KEY = unicode( os.environ['EZACS__COMMON_SHIB_ENTITLEMENT_KEY'] )
SHIB_EPPN_KEY = unicode( os.environ['EZACS__COMMON_SHIB_EPPN_KEY'] )
SHIB_MAIL_KEY = unicode( os.environ['EZACS__COMMON_SHIB_MAIL_KEY'] )
SHIB_MEMBEROF_KEY = unicode( os.environ['EZACS__COMMON_SHIB_MEMBEROF_KEY'] )
SHIB_NAMEFIRST_KEY = unicode( os.environ['EZACS__COMMON_SHIB_NAMEFIRST_KEY'] )
SHIB_NAMELAST_KEY = unicode( os.environ['EZACS__COMMON_SHIB_NAMELAST_KEY'] )
SHIB_NETID_KEY = unicode( os.environ['EZACS__COMMON_SHIB_NETID_KEY'] )
SHIB_PHONE_KEY = unicode( os.environ['EZACS__COMMON_SHIB_PHONE_KEY'] )
SHIB_SHORTID_KEY = unicode( os.environ['EZACS__COMMON_SHIB_SHORTID_KEY'] )
SHIB_STATUS_KEY = unicode( os.environ['EZACS__COMMON_SHIB_STATUS_KEY'] )
SHIB_TITLE_KEY = unicode( os.environ['EZACS__COMMON_SHIB_TITLE_KEY'] )
SHIB_TYPE_KEY = unicode( os.environ['EZACS__COMMON_SHIB_TYPE_KEY'] )


# ===============================================================================
# misc settings to properly categorize
# ===============================================================================

DELIVERY_SERVICE_CHECK_STRING = os.environ['EZACS__DELIVERY_SERVICE_CHECK_STRING']

## Previous note:
    #We will use this setting to redirect users coming from some IPs to the old
    #interface.  This is a temporary solution to the Shib logout issue.
## Don't know if the old url is still there.
CLASSIC_EZBORROW = os.environ['EZACS__CLASSIC_EZBORROW']  # url to old landing page.
CLASSIC_IPS = json.loads( os.environ['EZACS__CLASSIC_IPS_JSON'] )


## eof
