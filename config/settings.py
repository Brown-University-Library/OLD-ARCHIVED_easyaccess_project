# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json, os
import dj_database_url


## ============================================================================
## standard project-level settings
## ============================================================================

SECRET_KEY = os.environ['EZACS__SECRET_KEY']

temp_DEBUG = json.loads( os.environ['EZACS__DEBUG_JSON'] )
assert temp_DEBUG in [ True, False ], Exception( 'DEBUG env setting is, "%s"' )
DEBUG = temp_DEBUG

TEMPLATE_DEBUG = DEBUG

ADMINS = json.loads( os.environ['EZACS__ADMINS_JSON'] )
MANAGERS = ADMINS

SITE_ID = 1

DATABASES = json.loads( os.environ['EZACS__DATABASES_JSON'] )

TIME_ZONE = 'America/New_York'

## https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = os.environ['EZACS__STATIC_URL']
STATIC_ROOT = os.environ['EZACS__STATIC_ROOT']  # needed for collectstatic command

APPEND_SLASH = True

# MIDDLEWARE_CLASSES = (
#     'django.middleware.common.CommonMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'delivery.middleware.DeliveryShib',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'delivery.middleware.DeliveryShib',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
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
    # 'south',
    'shorturls',
    'shibboleth',
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
Note: to see the imported modules' loggers, add somewhere, like the top of 'findit/views.py':
    import logging
    existing_logger_names = logging.getLogger().manager.loggerDict.keys()
    print '- HERE, `%s`' % existing_logger_names
    (from <https://bytes.com/topic/python/answers/830042-dynamically-getting-loggers>)
"""
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
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
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
            'propagate': True,
        },
    'illiad': { # I keep all my apps here, but you can also add them one by one
            'handlers': ['illiad_log_file'],
            # 'level': 'DEBUG',
            'level': os.environ['EZACS__ILLIAD_LOG_LEVEL'],
            'propagate': True,
        },
    'access': { # I keep all my apps here, but you can also add them one by one
            'handlers': ['access_log_file'],
            # 'level': 'INFO',
            'level': os.environ['EZACS__ACCESS_LOG_LEVEL'],
            'propagate': True,
        },
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'shibboleth.backends.ShibbolethRemoteUserBackend',
    )

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    # 'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    # 'findit.context_processors.login_link',
    # 'findit.context_processors.debug_mode',
    # 'shibboleth.context_processors.login_link',
    # 'shibboleth.context_processors.logout_link',
    )

LOGIN_URL = os.environ['EZACS__LOGIN_URL']
LOGIN_REDIRECT_URL = os.environ['EZACS__LOGIN_REDIRECT_URL']

ALLOWED_HOSTS = json.loads( os.environ['EZACS__ALLOWED_HOSTS_JSON'] )

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
FINDIT_DB_PUSH_BOTTOM = ['EBSCOhost', 'LexisNexis']

FINDIT_GSCHOLAR = os.environ['EZACS__FINDIT_GSCHOLAR']

FINDIT_SKIP_SUMMON_DIRECT_LINK = ['summon', 'worldcat', 'pubmed']  # list of referring sites to not consult Summon for.


## ============================================================================
## shibboleth app settings
## ============================================================================

SHIB_MOCK_HEADERS = json.loads( os.environ['EZACS__SHIBBOLETH_MOCK_HEADERS_JSON'] )
SHIB_MOCK_MAP = json.loads( os.environ['EZACS__SHIBBOLETH_MOCK_MAP_JSON'] )


# ===============================================================================
# misc settings to properly categorize
# ===============================================================================

SHIB_EMAIL = os.environ['EZACS__SHIB_EMAIL']
SHIB_USERNAME = os.environ['EZACS__SHIB_USERNAME']
SHIBBOLETH_LOGOUT_URL = os.environ['EZACS__SHIBBOLETH_LOGOUT_URL']
SHIBBOLETH_ATTRIBUTE_MAP = json.loads( os.environ['EZACS__SHIBBOLETH_ATTRIBUTE_MAP_JSON'] )

DELIVERY_SERVICE_CHECK_STRING = os.environ['EZACS__DELIVERY_SERVICE_CHECK_STRING']

## Previous note:
    #We will use this setting to redirect users coming from some IPs to the old
    #interface.  This is a temporary solution to the Shib logout issue.
## Don't know if the old url is still there.
CLASSIC_EZBORROW = os.environ['EZACS__CLASSIC_EZBORROW']  # url to old landing page.
CLASSIC_IPS = json.loads( os.environ['EZACS__CLASSIC_IPS_JSON'] )

## for mocking shib
DEV_SERVERS = json.loads( os.environ['EZACS__DEV_SERVERS_JSON'] )
TEST_USER = tuple( json.loads(os.environ['EZACS__TEST_USER_JSON']) )


## eof
