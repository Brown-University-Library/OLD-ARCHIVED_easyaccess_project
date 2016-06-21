# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


DEBUG = getattr(settings, 'DEBUG', True)

#===============================================================================
# Adjust service status settings here.
#===============================================================================
#For turning the service on and off.  This will be helpful for solving problems
#that arise.  For now off means it will re-route to the Serial Solutions account
#specified in the BUL_LINK settings.
SERVICE_ACTIVE = getattr(settings, 'FINDIT_SERVICE_ACTIVE', True)
SERVICE_OFFLINE = getattr(settings, 'FINDIT_SERVICE_OFFLINE', False)
#Use for cases when 360Link and or Summon is known to be down.
#===============================================================================
# End service status settings.
#===============================================================================

SERSOL_KEY = os.environ['EZACS__BUL_LINK_SERSOL_KEY']

#For admin
STAFF_USERS = getattr(settings, 'FINDIT_STAFF_USERS', [])

LOGIN_URL = getattr(settings, 'LOGIN_URL', None)
if not LOGIN_URL:
    raise ImproperlyConfigured('LOGIN_URL is a required setting.  Protect it with Shib.')

PERMALINK_PREFIX = getattr(settings, 'FINDIT_PERMALINK_PREFIX', 'su')
PRINT_PROVIDER = getattr(settings, 'FINDIT_PRINT_PROVIDER', '')

ILLIAD_KEY = getattr(settings, 'FINDIT_ILLIAD_KEY', None)
#Don't set if you don't want to hand off book resolving.
BOOK_RESOLVER = getattr(settings, 'FINDIT_BOOK_RESOLVER', None)


ILLIAD_REMOTE_AUTH_URL = getattr(settings, 'FINDIT_ILLIAD_REMOTE_AUTH_URL', None)
if ILLIAD_REMOTE_AUTH_URL is None:
     raise ImproperlyConfigured('Illiad remote auth url is required.')
ILLIAD_REMOTE_AUTH_HEADER = getattr(settings, 'FINDIT_ILLIAD_REMOTE_AUTH_HEADER', None)
if ILLIAD_REMOTE_AUTH_HEADER is None:
     raise ImproperlyConfigured('Illiad remote auth header is required.')

ILLIAD_URL_ROOT = os.environ['EZACS__FINDIT_ILLIAD_URL']  # `http...OpenURL?%s`

EMAIL_FROM = getattr(settings, 'FINDIT_EMAIL_FROM', None)

if EMAIL_FROM is None:
     raise ImproperlyConfigured('From email is required: FINDIT_EMAIL_FROM.')

SHIB_ATTRIBUTE_MAP = getattr(settings, 'FINDIT_SHIB_ATTRIBUTE_MAP', None )

MENDELEY_CONSUMER_KEY = getattr(settings, 'FINDIT_MENDELEY_CONSUMER_KEY', None)
MENDELEY_SECRET_KEY =  getattr(settings, 'FINDIT_MENDELEY_SECRET_KEY', None)
MAS_KEY = getattr(settings, 'FINDIT_MAS_KEY', None)

#Summon
SUMMON_ID = getattr(settings, 'FINDIT_SUMMON_ID', None)
SUMMON_KEY = getattr(settings, 'FINDIT_SUMMON_KEY', None)
if not (SUMMON_ID or SUMMON_KEY):
    raise ImproperlyConfigured('Summon creditials are required SUMMON_ID and SUMMON_KEY.')

#For reporting problems
PROBLEM_URL = os.environ['EZACS__PROBLEM_REPORT_URL'] + '%s&entry_4=%s'

#Timeout for urllib2 requests to third party sources
EXTRAS_TIMEOUT = getattr(settings, 'FINDIT_EXTRAS_TIMEOUT', 10)

#For sorting databases returned by provider.
DB_SORT_BY = getattr(settings, 'FINDIT_DB_SORT_BY', [])
#Providers in this list will be forced to the top.
DB_PUSH_TOP = getattr(settings, 'FINDIT_DB_PUSH_TOP', [])
#Providers in this list will be forced to the bottom.
DB_PUSH_BOTTOM = getattr(settings, 'FINDIT_DB_PUSH_BOTTOM', [])

## if true, will take user directly to full text when it's found; if false, will show landing page.
FLY_TO_FULLTEXT = json.loads( os.environ['EZACS__FINDIT_GO_DIRECT_TO_FULLTEXT_JSON'] )


## EOF ###
