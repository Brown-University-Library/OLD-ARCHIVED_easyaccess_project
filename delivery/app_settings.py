# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


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

#For reporting problems
PROBLEM_URL = os.environ['EZACS__PROBLEM_REPORT_URL']

ILLIAD_URL = getattr(settings, 'FINDIT_ILLIAD_URL', None)
if ILLIAD_URL is None:
    raise ImproperlyConfigured("""Illiad URL required.  Add to settings as FIDIT_ILLIAD_URL as
    http://your.school.edu/illiad.dll/OpenURL?%s""")

#Check to see if a user can request items.
SERVICE_CHECK_STRING = getattr(settings, 'DELIVERY_SERVICE_CHECK_STRING', None)

#Timeout for urllib2 requests to third party sources
#EXTRAS_TIMEOUT = getattr(settings, 'FINDIT_EXTRAS_TIMEOUT', 10)

AVAILABILITY_URL_ROOT = os.environ['EZACS__BORROW_AVAILABILITY_URL_ROOT']
