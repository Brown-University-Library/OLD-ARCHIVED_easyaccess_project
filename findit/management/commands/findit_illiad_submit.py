# # -*- coding: utf-8 -*-

# from __future__ import unicode_literals

# """
# Handle Illiad submissions.


# -- add delay and run continuously in the background.

# -- need to add unit tests to the newest py360link2 to make sure it's returning
# print issns.

# """
# #django
# from django.core.management.base import BaseCommand
# from django.contrib.auth.models import User
# from django.core.exceptions import ObjectDoesNotExist
# # from django.utils.log import dictConfig
# from django.conf import settings
# #stdlib
# from optparse import make_option
# import sys

# #local
# from findit.app_settings import ILLIAD_REMOTE_AUTH_URL, ILLIAD_REMOTE_AUTH_HEADER
# from illiad.account import IlliadSession
# from findit.utils import make_illiad_url
# #from delivery.utils import make_illiad_url

# #logging
# import logging
# # dictConfig(settings.LOGGING)
# ilog = logging.getLogger('illiad')

# #from delivery.new360link import py360link2
# #import bibjsontools
# from py360link2 import get_sersol_data, Resolved

# sersol_key=settings.BUL_LINK_SERSOL_KEY
# import urllib2
# import sys


# class Command(BaseCommand):
#     help = "For submitting ILLiad findit database."

#     def handle(self, **options):
#         from findit.models import Request
#         count = 0
#         new_requests = Request.objects.filter(illiad_tn='new')
#         for request in new_requests:
#             user = request.user
#             profile = user.libraryprofile
#             illiad_profile = profile.illiad()
#             tries = 0
#             while tries < 3:
#                 try:
#                     sersol = get_sersol_data(request.item.query, key=sersol_key)
#                     break
#                 except urllib2.URLError:
#                     print>>sys.stderr, "360Link timeout.  Trying again."
#                     tries += 1
#             resolved = Resolved(sersol)
#             illiad_request_url = "%s&sid=%s" % (make_illiad_url(resolved.openurl), request.item.referrer)
#             #print bib
#             #print illiad_request_url
#             #print illiad_request_url
#             ill_username = illiad_profile['username']
#             #Get the OpenURL we will submit.
#             ill_url = illiad_request_url
#             ilog.info('User %s posted %s for request.' % (ill_username,
#                                                            ill_url))
#             out = {}
#             #Get an illiad instance
#             illiad = IlliadSession(ILLIAD_REMOTE_AUTH_URL,
#                                    ILLIAD_REMOTE_AUTH_HEADER,
#                                    ill_username)
#             illiad_session = illiad.login()
#             ilog.info('User %s established Illiad session: %s.' % (ill_username,
#                                                                   illiad_session['session_id']))
#             out['session'] = illiad_session

#             if not illiad_session['authenticated']:
#                 out['session_error'] = 'Failed login.'
#                 ilog.error("Illiad login failed for %s" % ill_username)
#             else:
#                 #Register users if neccessary.
#                 if not illiad.registered:
#                     ilog.info('Will register %s with illiad.' % (ill_username))
#                     ilog.info('Registering %s with Illiad as %s.' % (ill_username,
#                                                                      illiad_profile['status'])
#                               )
#                     reg = illiad.register_user(illiad_profile)
#                     ilog.info('%s registration response: %s' % (ill_username, reg))

#                 illiad_post_key = illiad.get_request_key(ill_url)
#                 #If blocked comes back in the post key, stop here with appropriate status.
#                 blocked = illiad_post_key.get('blocked', None)
#                 errors = illiad_post_key.get('errors', None)
#                 if blocked:
#                     out['blocked'] = blocked
#                     ilog.info("%s is blocked in Illiad." % ill_username)
#                     self.send_message('blocked', resource=resource)
#                 elif errors:
#                     out['errors'] = True
#                     msg = illiad_post_key['message']
#                     ilog.info("Request errors during Illiad submission: %s %s" %\
#                                 (ill_username,
#                                  self.msg))
#                     out['message'] = msg
#                 else:
#                     #Submit this
#                     submit_status = illiad.make_request(illiad_post_key)
#                     out['submit_status'] = submit_status
#                     #Write the request to the requests table.
#                     if submit_status['submitted']:
#                         illiad_tn = submit_status['transaction_number']
#                         request.illiad_tn = illiad_tn
#                         print request.user, request.id, request.item.id, illiad_tn
#                         request.save()
#                         count += 1
#                     else:
#                         ilog.error("%s request failed with message %s." %\
#                                    (ill_username,
#                                    submit_status['message']))

#             illiad.logout()
#             #if count == 10: break
