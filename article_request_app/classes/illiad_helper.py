# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from article_request_app import settings_app
from django.core.urlresolvers import reverse
from illiad.account import IlliadSession


log = logging.getLogger('access')


class IlliadHelper( object ):
    """ Contains helpers for views.illiad_request(), views.login() and views.illiad_handler() """

    def __init__(self):
        self.problem_message = """
Your request was not able to be submitted to ILLiad, our Interlibrary Loan system.

Please try again later, and if the problem persists:

- let us know at the easyArticle feedback/problem link.

- Contact Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

Apologies for the inconvenience.
"""

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /find/.
            Called by views.illiad_request() """
        ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
        log.debug( 'last_path, `{}`'.format(last_path) )
        if last_path == '/easyaccess/article_request/login_handler/':
            referrer_ok = True
        if referrer_ok is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
        return ( referrer_ok, redirect_url )

    def login_user( self, request, shib_dct ):
        """ Logs user into illiad;
            Checks for and handles 'blocked' and 'newuser' status;
            Updates session with 'problem_message' if necessary.
            Called by views.login() """
        success = False
        ( illiad_instance, illiad_session ) = self._connect( request, shib_dct )
        if illiad_session is not False:
            if self._check_blocked(request, illiad_session) is False:
                if self._handle_new_user(request, shib_dct, illiad_instance) is True:
                    success = True
        log.debug( 'success, `%s`' % success )
        return ( illiad_instance, success )

    # def _connect( self, request, shib_dct ):
    #     """ Starts login.
    #         Called by login_user() """
    #     illiad_session = False
    #     ill_username = shib_dct['eppn'].split('@')[0]
    #     illiad_instance = IlliadSession( settings_app.ILLIAD_REMOTE_AUTH_URL, settings_app.ILLIAD_REMOTE_AUTH_HEADER, ill_username )
    #     try:
    #         illiad_session = illiad_instance.login()
    #     except Exception as e:
    #         log.error( 'Exception on illiad login, ```%s```' % unicode(repr(e)) )
    #         request.session['problem_message'] = 'Problem accessing ILLiad, please try this request later.'
    #     log.debug( 'illiad_instance.__dict__, ```%s```' % pprint.pformat(illiad_instance.__dict__) )
    #     log.debug( 'illiad_session, ```%s```' % pprint.pformat(illiad_session) )
    #     return ( illiad_instance, illiad_session )

    def _connect( self, request, shib_dct ):
        """ Starts login.
            Called by login_user() """
        illiad_session = False
        ill_username = shib_dct['eppn'].split('@')[0]
        illiad_instance = IlliadSession( settings_app.ILLIAD_REMOTE_AUTH_URL, settings_app.ILLIAD_REMOTE_AUTH_HEADER, ill_username )
        try:
            illiad_session = illiad_instance.login()
        except Exception as e:
            log.error( 'Exception on illiad login, ```%s```' % unicode(repr(e)) )
            request.session['message'] = self.problem_message
        log.debug( 'illiad_instance.__dict__, ```%s```' % pprint.pformat(illiad_instance.__dict__) )
        log.debug( 'illiad_session, ```%s```' % pprint.pformat(illiad_session) )
        return ( illiad_instance, illiad_session )

    # def _check_blocked( self, request, illiad_session ):
    #     """ Checks for blocked status and updates session if necessary.
    #         Called by login_user() """
    #     blocked = illiad_session.get('blocked', False)
    #     if blocked is True:
    #         citation_json = request.session.get( 'citation', '{}' )
    #         message = self.make_illiad_blocked_message(
    #             shib_dct['firstname'], shib_dct['lastname'], json.loads(citation_json) )
    #         request.session['problem_message'] = message
    #     log.debug( 'blocked, `%s`' % blocked )
    #     return blocked

    def _check_blocked( self, request, illiad_session ):
        """ Checks for blocked status and updates session if necessary.
            Called by login_user() """
        blocked = illiad_session.get('blocked', False)
        if blocked is True:
            citation_json = request.session.get( 'citation', '{}' )
            message = self.make_illiad_blocked_message(
                shib_dct['firstname'], shib_dct['lastname'], json.loads(citation_json) )
            request.session['message'] = message
        log.debug( 'blocked, `%s`' % blocked )
        return blocked

    # def _handle_new_user( self, request, shib_dct, illiad_instance ):
    #     """ Registers new user if necessary.
    #         Called by login_user() """
    #     handled = True
    #     if not illiad_instance.registered:
    #         illiad_instance = self._register_new_user( illiad_instance, shib_dct )
    #         if not illiad_instance.registered:
    #             handled = False
    #             log.info( 'auto-registration for `%s` was not successful; will build web-page message' % ill_username )
    #             message = self.make_illiad_unregistered_message(
    #                 shib_dct['firstname'], shib_dct['lastname'], json.loads(citation_json) )
    #             request.session['problem_message'] = message
    #     log.debug( 'handled, `%s`' % handled )
    #     return handled

    def _handle_new_user( self, request, shib_dct, illiad_instance ):
        """ Registers new user if necessary.
            Called by login_user() """
        handled = True
        if not illiad_instance.registered:
            illiad_instance = self._register_new_user( illiad_instance, shib_dct )
            if not illiad_instance.registered:
                handled = False
                log.info( 'auto-registration for `%s` was not successful; will build web-page message' % ill_username )
                message = self.make_illiad_unregistered_message(
                    shib_dct['firstname'], shib_dct['lastname'], json.loads(citation_json) )
                request.session['message'] = message
        log.debug( 'handled, `%s`' % handled )
        return handled

    def _register_new_user( self, illiad_instance, shib_dct ):
        """ Registers new user.
            Called by _handle_new_user() """
        try:
            illiad_profile = {
                'first_name': shib_dct['name_first'], 'last_name': shib_dct['name_last'],
                'email': shib_dct['email'], 'status': shib_dct['brown_type'],
                'phone': shib_dct['phone'], 'department': shib_dct[''], }
            log.info( 'will register new-user `%s` with illiad with illiad_profile, ```%s```' % (ill_username, pprint.pformat(illiad_profile)) )
            reg_response = illiad_instance.register_user( illiad_profile )
            log.info( 'illiad registration response for `%s` is `%s`' % (ill_username, reg_response) )
        except Exception as e:
            log.error( 'Exception on new user registration, ```%s```' % unicode(repr(e)) )
        return illiad_instance

    def logout_user( self, illiad_instance ):
        """ Logs out user & logs any errors.
            Called by views.login() """
        try:
            illiad_instance.logout()
            log.debug( 'illiad logout successful' )
        except Exception as e:
            log.error( 'illiad logout exception, ```%s```' % unicode(repr(e)) )
        return

    ##########################
    ### illiad blocked message
    ##########################
    def make_illiad_blocked_message( self, firstname, lastname, citation ):
        """ Preps illiad blocked message.
            Called by _check_blocked() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyArticle service. It appears there is a problem with your Interlibrary Loan, ILLiad account.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    ''' % (
        firstname,
        lastname,
        citation )
        log.debug( 'illiad blocked message built, ```%s```' % message )
        return message

    ###############################
    ### illiad unregistered message
    ###############################
    def make_illiad_unregistered_message( self, firstname, lastname, citation ):
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
        citation )
        log.debug( 'illiad unregistered message built, ```%s```' % message )
        return message

    ##########################
    ### illiad success message
    ##########################
    def make_illiad_success_message( self, firstname, lastname, citation_jsn, illiad_transaction_number, email ):
        """ Preps illiad success message.
            Called by views.illiad_handler() """
        citation_dct = json.loads( citation_jsn )
        if citation_dct.get( 'title', '' ) != '':
            title = citation_dct['title']
        else:
            title = citation_dct['source']
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

    ## end class IlliadHelper
