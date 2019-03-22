# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
import requests
from article_request_app import settings_app
from common_classes.illiad_helper import IlliadHelper as CommonIlliadHelper
from django.core.urlresolvers import reverse
from illiad.account import IlliadSession
# from requests.auth import HTTPBasicAuth


log = logging.getLogger('access')
common_illiad_helper = CommonIlliadHelper()


class IlliadApiHelper( object ):
    """ Contains helpers for views.login_handler() (for now; more later).
        Purpose is to use this to transition away from pip-installed illiad module to illiad-api-webservice calls. """

    def __init__(self):
        pass

    def manage_illiad_user_check( self, usr_dct, title ):
        """ Manager for illiad handling.
            - hits the new illiad-api for the status (`blocked`, `registered`, etc)
            - if problem, prepares failure message as-is (creating return-dct)
            - for now, hit common_classes.illiad_helper.IlliadHelper.check_illiad( shib_dct ) (creating return-dct)
              - this will create a new-user if necessary...
              - and also check and update a user's type (eg 'Staff', 'Undergraduate') if necessary
            Called by views.login_handler() """
        log.debug( '(article_request_app) - usr_dct, ```%s```' % pprint.pformat(usr_dct) )
        illiad_status_dct = self.check_illiad_status( usr_dct['eppn'].split('@')[0] )
        if illiad_status_dct['response']['blocked'] is True or illiad_status_dct['response']['disavowed'] is True:
            return_dct = self._prepare_failure_message( connect_result_dct, user_dct, title, return_dct )
        else:
            common_illiad_helper.check_illiad( user_dct )
            return_dct = { 'success': True }
        log.debug( 'return_dct, ```%s```' % pprint.pformat(return_dct) )
        return return_dct

    def check_illiad_status( self, auth_id ):
        url = '%s%s' % ( settings_app.ILLIAD_API_URL_ROOT, 'check_user/' )
        params = {
            'user': auth_id
            }
        try:
            r = requests.get( url, params=params, auth=(settings_app.ILLIAD_API_BASIC_AUTH_USER, settings_app.ILLIAD_API_BASIC_AUTH_PASSWORD), verify=True, timeout=10 )
            log.debug( 'status_code, `%s`; content, ```%s```' % (r.status_code, r.content.decode('utf-8', 'replace')) )
        except Exception as e:
            log.error( 'error on status check, ```%s```' % repr(e) )
        return


    ## end class IlliadApiHelper()


class NewIlliadHelper( object ):
    """ Contains helpers for views.illiad_request(), views.login() and views.illiad_handler()
        New code with unit-tests.
        Under construction. """

    def __init__(self):
        self.problem_message = """
Your request was not able to be submitted to ILLiad, our Interlibrary Loan system.

Please try again later. If the problem persists, there may be an issue with your ILLiad account.

Contact Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

Apologies for the inconvenience.
"""

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /find/.
            Called by views.illiad_request() """
        # ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
        ( referrer_ok, redirect_url, last_path ) = ( False, '', session_dct.get('last_path', '') )
        log.debug( 'last_path, `{}`'.format(last_path) )
        if last_path == '/easyaccess/article_request/login_handler/' or last_path == '/article_request/login_handler/':  # production vs dev-runserver; TODO: handle better.
            referrer_ok = True
        if referrer_ok is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
        return ( referrer_ok, redirect_url )

    # def login_user( self, user_dct, title ):
    #     """ Logs user into illiad;
    #         Checks for and handles 'blocked' and 'newuser' status;
    #         Returns 'problem_message' if necessary.
    #         Called by views.login_handler() """
    #     return_dct = { 'illiad_session_instance': None, 'error_message': None, 'success': False }
    #     connect_result_dct = self._connect( ill_username=user_dct['eppn'].split('@')[0] )
    #     return_dct['illiad_session_instance'] = connect_result_dct['illiad_session_instance']
    #     if connect_result_dct['illiad_session_instance'] is False or connect_result_dct['is_blocked'] is True or connect_result_dct['error_message'] is not None:
    #         return_dct = self._prepare_failure_message( connect_result_dct, user_dct, title, return_dct )
    #     elif connect_result_dct['is_new_user'] is True or connect_result_dct['is_registered'] is False:
    #         return_dct = self._handle_new_user( connect_result_dct['illiad_session_instance'], user_dct, title, return_dct )
    #     else:
    #         return_dct['success'] = True
    #     log.debug( 'return_dct, ```{}```'.format(pprint.pformat(return_dct)) )
    #     return return_dct

    def login_user( self, user_dct, title ):
        """ Manager for illiad handling.
            - Logs user into illiad;
            - Checks for and handles 'blocked' and 'newuser' status;
            - Returns 'problem_message' if necessary.
            - If user is ok, checks and updates, if necessary, status.
            Called by views.login_handler() """
        log.debug( 'in article_request_app.classes.illiad_helper; user_dct, ```%s```' % pprint.pformat(user_dct) )
        ( return_dct, connect_result_dct ) = ( {'illiad_session_instance': None, 'error_message': None, 'success': False}, self._connect(ill_username=user_dct['eppn'].split('@')[0]) )
        return_dct['illiad_session_instance'] = connect_result_dct['illiad_session_instance']
        if connect_result_dct['illiad_session_instance'] is False or connect_result_dct['is_blocked'] is True or connect_result_dct['error_message'] is not None:
            return_dct = self._prepare_failure_message( connect_result_dct, user_dct, title, return_dct )
        elif connect_result_dct['is_new_user'] is True or connect_result_dct['is_registered'] is False:
            return_dct = self._handle_new_user( connect_result_dct['illiad_session_instance'], user_dct, title, return_dct )
        else:
            return_dct['success'] = True
        common_illiad_helper.check_illiad( user_dct )
        log.debug( 'return_dct, ```{}```'.format(pprint.pformat(return_dct)) )
        return return_dct

    def _connect( self, ill_username ):
        """ Makes session-connection, and tries login.
            Called by login_user() """
        return_dct = { 'error_message': None, 'illiad_login_dct': None, 'illiad_session_instance': False, 'is_blocked': None, 'is_logged_in': None, 'is_new_user': None, 'is_registered': None, 'submitted_username': ill_username }
        illiad_session_instance = IlliadSession( settings_app.ILLIAD_REMOTE_AUTH_URL, settings_app.ILLIAD_REMOTE_AUTH_HEADER, ill_username )  # illiad_session_instance.registered will always be False before login attempt
        log.debug( 'illiad_session_instance.__dict__, ```{}```'.format(pprint.pformat(illiad_session_instance.__dict__)) )
        return_dct['illiad_session_instance'] = illiad_session_instance
        # return_dct['is_blocked'] = illiad_session_instance.blocked_patron
        try:
            return_dct = self._login( illiad_session_instance, return_dct )
        except Exception as e:
            log.error( 'Exception on illiad login, ```%s```' % unicode(repr(e)) )
            return_dct['error_message'] = self.problem_message
        log.debug( 'return_dct, ```{}```'.format(pprint.pformat(return_dct)) )
        return return_dct

    def _login( self, illiad_session_instance, return_dct ):
        """ Tries login.
            Called by _connect() """
        illiad_login_dct = illiad_session_instance.login()
        # return_dct['is_blocked'] = illiad_login_dct['blocked']
        return_dct['is_blocked'] = illiad_login_dct.get( 'blocked', illiad_session_instance.blocked_patron )  # will update value if it's in login_dct
        return_dct['illiad_login_dct'] = illiad_login_dct
        return_dct['is_logged_in'] = illiad_login_dct['authenticated']
        return_dct['is_new_user'] = illiad_login_dct['new_user']
        return_dct['is_registered'] = illiad_login_dct.get('registered', False)
        return return_dct

    def _prepare_failure_message( self, connect_result_dct, user_dct, title, return_dct ):
        """ Sets return error_message on connect/login failure.
            Called by login_user() """
        if connect_result_dct['error_message'] is not None:
            return_dct['error_message'] = connect_result_dct['error_message']
        elif connect_result_dct['is_blocked'] is True:
            return_dct['error_message'] = self.make_illiad_blocked_message( user_dct['name_first'], user_dct['name_last'], title )
        log.debug( 'return_dct, ```{}```'.format(pprint.pformat(return_dct)) )
        return return_dct

    def _handle_new_user( self, illiad_session_instance, user_dct, item_dct, return_dct ):
        """ Attempts to register new user, and prepares appropriate return_dct based on result.
            Called by login_user() """
        updated_illiad_session_instance = self._register_new_user( illiad_session_instance, user_dct )
        if updated_illiad_session_instance.registered is False:
            return_dct['error_message'] = self.make_illiad_unregistered_message( firstname, lastname, title )
        else:
            return_dct['success'] = True
        log.debug( 'return_dct, ```{}```'.format(pprint.pformat(return_dct)) )
        return return_dct

    def _register_new_user( self, illiad_session_instance, user_dct ):
        """ Registers new user.
            Called by _handle_new_user() """
        try:
            illiad_profile = {
                'first_name': user_dct['name_first'], 'last_name': user_dct['name_last'],
                'email': user_dct['email'], 'status': user_dct['brown_type'],
                'phone': user_dct['phone'], 'department': user_dct['department'], }
            log.info( 'will register new-user `%s` with illiad with illiad_profile, ```%s```' % (illiad_session_instance.username, pprint.pformat(illiad_profile)) )
            reg_response = illiad_session_instance.register_user( illiad_profile )
            log.info( 'illiad registration response for `%s` is `%s`' % (illiad_session_instance.username, reg_response) )
        except Exception as e:
            log.error( 'Exception on new user registration, ```%s```' % unicode(repr(e)) )
        log.debug( 'illiad_session_instance.__dict__ AFTER registration, ```{}```'.format(pprint.pformat(illiad_session_instance.__dict__)) )
        return illiad_session_instance

    # def check_illiad_status( self, user_dct ):
    #     """ Checks and updates illiad status if necessary.
    #         Called by login_user() """
    #     common_illiad_helper.check_illiad( user_dct )
    #     return

    def logout_user( self, illiad_instance ):
        """ Logs out user & logs any errors.
            Called by views.login_handler() """
        try:
            illiad_instance.logout()
            log.debug( 'illiad logout successful' )
        except Exception as e:
            log.error( 'illiad logout exception, ```%s```' % unicode(repr(e)) )
        return

    ##########################
    ### illiad blocked message
    ##########################
    def make_illiad_blocked_message( self, firstname, lastname, title ):
        """ Preps illiad blocked message.
            Called by _check_blocked() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyArticle service. It appears there is a problem with your Interlibrary Loan, ILLiad account.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    '''.strip() % (
        firstname,
        lastname,
        title )
        log.debug( 'illiad blocked message built, ```%s```' % message )
        return message

    ###############################
    ### illiad unregistered message
    ###############################
    def make_illiad_unregistered_message( self, firstname, lastname, title ):
        """ Preps illiad blocked message.
            Called by _handle_new_user() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyAccess service. There was a problem trying to register you with 'ILLiad', our interlibrary-loan service.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    ''' % (
        firstname,
        lastname,
        title )
        log.debug( 'illiad unregistered message built, ```%s```' % message )
        return message

    ##########################
    ### illiad success message
    ##########################
    def make_illiad_success_message( self, firstname, lastname, title, illiad_transaction_number, email ):
        """ Preps illiad success message.
            Called by views.illiad_handler() """
        message = '''
Greetings {firstname} {lastname},

We're getting the title '{title}' for you. You'll be notified when it arrives.

Some useful information for your records:

- Title: '{title}'
- Ordered from service: 'ILLiad'
- Your Illiad reference number: '{illiad_num}'
- Notification of arrival will be sent to email address: <{email}>

You can check your Illiad account at the link:
<https://illiad.brown.edu/illiad/>

If you have any questions, contact the Library's Interlibrary Loan office at <interlibrary_loan@brown.edu> or call 401-863-2169.

  '''.format(
        firstname=firstname,
        lastname=lastname,
        title=title,
        illiad_num=illiad_transaction_number,
        email=email )
        log.debug( 'illiad success message built' )
        return message

    ## end class NewIlliadHelper
