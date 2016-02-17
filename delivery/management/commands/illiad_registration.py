# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Handle Illiad registration.
"""
#django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
#stdlib
from optparse import make_option
import sys
from pprint import pprint
from datetime import date, timedelta

"""
Register or update registration for users in the easyA database.
"""
from delivery.models import LibraryProfile
from findit.app_settings import ILLIAD_REMOTE_AUTH_URL, ILLIAD_REMOTE_AUTH_HEADER
from illiad.account import IlliadSession

#logging
from django.conf import settings
# from django.utils.log import dictConfig
import logging
# dictConfig(settings.LOGGING)
#logging illiad.
ilog = logging.getLogger('illiad')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


#Day interval to re-register users.
DAYS = 180

class Command(BaseCommand):
    help = "For registering users with ILLiad."
    option_list = BaseCommand.option_list + (
        make_option('--max', '-m', dest='max',
            help='Maximum users to register.  Useful for debugging.'),
    )
    def handle(self, **options):
        #Time delta for querying users that haven't been registerd in X
        #number of days.
        today = date.today()
        cutoff = today - timedelta(days=DAYS)
        #Exclude any users who have been registered or updated after
        #the cutoff date.
        profiles = LibraryProfile.objects.exclude(
                illiad_registration_date__gte=cutoff
                )
        for user_profile in profiles:
            user = user_profile.user
            #Skip local admin users.
            if user.username.find('@brown.edu') < 0:
                continue
            illiad_key = user_profile.illiad()
            ill_session = IlliadSession(ILLIAD_REMOTE_AUTH_URL,
                               ILLIAD_REMOTE_AUTH_HEADER,
                               illiad_key.get('username'))
            status = ill_session.login()
            if status.get('registered') == False:
                logging.info("Will register %s with ILLiad as %s." % (user.username, illiad_key))
                registration = ill_conn.register_user(illiad_key)
            else:
                #update registration
                logging.info("Updating ILLiad registration for %s with %s." % (user.username, illiad_key))

            #Update the illiad registration information.
            user_profile.illiad_registration_date = today
            user_profile.save()

            ill_session.logout()
