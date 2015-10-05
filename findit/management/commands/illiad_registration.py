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

#local
from findit.models import UserProfile
from findit.app_settings import ILLIAD_REMOTE_AUTH_URL, ILLIAD_REMOTE_AUTH_HEADER
from illiad.account import IlliadSession

class Command(BaseCommand):
    help = "For registering Illiad users from the findit database."
    option_list = BaseCommand.option_list + (
        make_option('--username', '-u', dest='username',
            help='Pass in username to register.  Must exist in database.'),
    )
    def handle(self, **options):
        if options['username']:
          self.register_user(options['username'])


    def register_user(self, username):
        from findit.models import Request
        new_requests = Request.objects.filter(illiad_tn='new')
        for request in new_requests:
            user = request.user
            username = request.user.username
            print username
#            username += '@brown.edu'
#            try:
#                user = User.objects.get(username=username)
#            except:
#                print>>sys.stderr, "%s was not found in the easyArticle database." % username
#                return
            profile = user.profile
            illiad_profile = profile.illiad()
            ill_username = illiad_profile['username']

            #Get an illiad instance
            sess = IlliadSession(ILLIAD_REMOTE_AUTH_URL,
                                   ILLIAD_REMOTE_AUTH_HEADER,
                                   ill_username)
            illiad_session = sess.login()

            #if not sess.registered:
            print>>sys.stderr, "Registering %s with Illliad as %s." % (username, illiad_profile)
            reg = sess.register_user(illiad_profile)
            print reg
            #else:
            #    print>>sys.stderr, "%s is already registered with Illiad." % username
            sess.logout()
            break
