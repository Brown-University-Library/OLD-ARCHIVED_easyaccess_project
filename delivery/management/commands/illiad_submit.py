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

#local
from findit.models import UserProfile
from findit.app_settings import ILLIAD_REMOTE_AUTH_URL, ILLIAD_REMOTE_AUTH_HEADER
from delivery.models import Request
from illiad.account import IlliadSession


class Command(BaseCommand):
    help = "For submitting existing requests to Illiad."
    option_list = BaseCommand.option_list + (
        make_option('--request', '-r', dest='request',
            help='Pass in request ID to send to Illiad.'),
    )
    def handle(self, **options):
        if options['request']:
          self.submit_to_illiad(options['request'])


    def submit_to_illiad(self, request_id):
        print "Submitting: ", request_id
        try:
            request = Request.objects.get(id=request_id)
        except ObjectDoesNotExist:
            print>>sys.stderr, "%s was not found in the easyArticle database." % request
            return
        profile = request.user.libraryprofile
        illiad_profile = profile.illiad()
        ill_username = illiad_profile['username']

        #Get an illiad instance
        sess = IlliadSession(ILLIAD_REMOTE_AUTH_URL,
                               ILLIAD_REMOTE_AUTH_HEADER,
                               ill_username)
        illiad_session = sess.login()

        #query
        query = request.bib['_query']

        #get the request key
        rk = sess.get_request_key(query)
        #submit the request
        submit = sess.make_request(rk)

        pprint(submit)

        sess.logout()
