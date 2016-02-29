# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from article_request_app import settings_app
from illiad.account import IlliadSession


log = logging.getLogger('access')


class IlliadHelper( object ):
    """ Contains helpers for views.login() """

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
            request.session['problem_message'] = 'Problem accessing ILLiad, please try this request later.'
        log.debug( 'illiad_instance.__dict__, ```%s```' % pprint.pformat(illiad_instance.__dict__) )
        log.debug( 'illiad_session, ```%s```' % pprint.pformat(illiad_session) )
        return ( illiad_instance, illiad_session )

    def _check_blocked( self, request, illiad_session ):
        """ Checks for blocked status and updates session if necessary.
            Called by login_user() """
        blocked = illiad_session.get('blocked', False)
        if blocked is True:
            citation_json = request.session.get( 'citation', '{}' )
            message = self.make_illiad_blocked_message(
                shib_dct['firstname'], shib_dct['lastname'], json.loads(citation_json) )
            request.session['problem_message'] = message
        log.debug( 'blocked, `%s`' % blocked )
        return blocked

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
                request.session['problem_message'] = message
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

    def make_illiad_blocked_message( self, firstname, lastname, citation ):
        """ Preps illiad blocked message.
            Called by build_message() """
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
        ### end make_illiad_blocked_message() ###

    def make_illiad_unregistered_message( self, firstname, lastname, citation ):
        """ Preps illiad blocked message.
            Called by build_message() """
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
        ### end make_illiad_unregistered_message() ###