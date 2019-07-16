# -*- coding: utf-8 -*-

import json, os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


SHIB_LOGIN_URL = os.environ['EZACS__BORROW_SHIB_LOGIN_URL']
SHIB_LOGOUT_URL_ROOT = os.environ['EZACS__COMMON_SHIB_LOGOUT_URL_ROOT']
SHIB_LOGOUT_URL_RETURN_ROOT = os.environ['EZACS__BORROW_SHIB_LOGOUT_URL_RETURN_ROOT']
DEVELOPMENT_SHIB_DCT = json.loads( os.environ['EZACS__COMMON_DEVELOPMENT_SHIB_JSON'] )

AVAILABILITY_URL_ROOT = os.environ['EZACS__BORROW_AVAILABILITY_URL_ROOT']

PROBLEM_FORM_URL_ROOT = os.environ['EZACS__BORROW_PROBLEM_FORM_URL_ROOT']
PROBLEM_FORM_KEY = os.environ['EZACS__BORROW_PROBLEM_FORM_KEY']


# ===========================
# illiad remote-auth settings
# ===========================

ILLIAD_KEY = getattr(settings, 'FINDIT_ILLIAD_KEY', None)

ILLIAD_REMOTE_AUTH_URL = getattr(settings, 'FINDIT_ILLIAD_REMOTE_AUTH_URL', None)
if ILLIAD_REMOTE_AUTH_URL is None:
     raise ImproperlyConfigured('Illiad remote auth url is required.')

ILLIAD_REMOTE_AUTH_HEADER = getattr(settings, 'FINDIT_ILLIAD_REMOTE_AUTH_HEADER', None)
if ILLIAD_REMOTE_AUTH_HEADER is None:
     raise ImproperlyConfigured('Illiad remote auth header is required.')

EMAIL_FROM = getattr(settings, 'FINDIT_EMAIL_FROM', None)
if EMAIL_FROM is None:
     raise ImproperlyConfigured('From email is required: FINDIT_EMAIL_FROM.')

ILLIAD_URL = getattr(settings, 'FINDIT_ILLIAD_URL', None)
if ILLIAD_URL is None:
    raise ImproperlyConfigured("""Illiad URL required.  Add to settings as FIDIT_ILLIAD_URL as
    http://your.school.edu/illiad.dll/OpenURL?%s""")

# ===========================


## illiad-api (eventually all illiad calls will be to the API)
ILLIAD_API_URL = os.environ['EZACS__COMMON_ILLIAD_API_URL_ROOT']
ILLIAD_API_KEY = os.environ['EZACS__COMMON_ILLIAD_API_KEY']


#Check to see if a user can request items.
SERVICE_CHECK_STRING = getattr(settings, 'DELIVERY_SERVICE_CHECK_STRING', None)

#Timeout for urllib2 requests to third party sources
#EXTRAS_TIMEOUT = getattr(settings, 'FINDIT_EXTRAS_TIMEOUT', 10)

SERSOL_KEY = os.environ['EZACS__BUL_LINK_SERSOL_KEY']

REQUIRED_GROUPER_GROUP = os.environ['EZACS__BORROW_REQUIRED_GROUP']
PERMISSION_DENIED_PHONE = os.environ['EZACS__BORROW_PERMISSION_DENIED_PHONE']
PERMISSION_DENIED_EMAIL = os.environ['EZACS__BORROW_PERMISSION_DENIED_EMAIL']
