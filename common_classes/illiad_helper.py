# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from common_classes import settings_common_tests as settings_app
from illiad.account import IlliadSession


log = logging.getLogger('access')


class IlliadHelper( object ):
    """ Contains helpers for delivery.views.process_request()
        TODO, move article-requet checks to here, too. """

    def __init__(self):
        pass

    def check_illiad( self, user_dct ):
        """ Logs user into illiad to check for, and handle, 'newuser' status.
            Returns True if it's not a new-user, or if it is a new-user and the new-user is registered successfully.
            Called by delivery.views.process_request() """
        ( illiad_session_instance, connect_ok ) = self.connect( ill_username=user_dct['eppn'].split('@')[0] )
        if connect_ok is False: return False
        ( illiad_session_instance, login_dct, login_ok ) = self.login( illiad_session_instance )  # login_dct only returned for testing purposes
        if login_ok is False: return False
        if illiad_session_instance.registered is True:
            log.info( 'not a new-user' )
            check_ok = True  # the check succeeded, nothing needs done (other than logout)
        else:
            check_ok = self.register_new_user( illiad_session_instance, user_dct )  # registers new user and returns True on success
        self.logout_user( illiad_session_instance )
        return check_ok

    def connect( self, ill_username ):
        """ Initializes illiad-session instance -- does not yet contact ILLiad.
            Called by check_illiad() """
        illiad_session_instance = IlliadSession( settings_app.ILLIAD_REMOTE_AUTH_URL, settings_app.ILLIAD_REMOTE_AUTH_HEADER, ill_username )  # illiad_session_instance.registered will always be False before login attempt
        ok = True
        log.debug( 'illiad_session_instance.__dict__, ```{}```'.format(pprint.pformat(illiad_session_instance.__dict__)) )
        log.debug( 'ill_username, `{name}`; ok, `{ok}`'.format(name=ill_username, ok=ok) )
        return ( illiad_session_instance, ok )

    def login( self, illiad_session_instance ):
        """ Tries login.
            Called by check_illiad() """
        try:
            login_dct = illiad_session_instance.login()
            log.debug( 'illiad_session_instance.__dict__, ```{}```'.format(pprint.pformat(illiad_session_instance.__dict__)) )
            ok = True
        except Exception as e:
            log.error( 'exception on illiad login, ```{}```'.format(unicode(repr(e))) )
            ( illiad_session_instance, login_dct, ok ) = ( None, None, False )
        log.debug( 'illiad_session_instance, `{}`'.format(illiad_session_instance) )
        log.debug( 'login_dct, ```{}```'.format(pprint.pformat(login_dct)) )
        log.debug( 'ok, `{}`'.format(ok) )
        return ( illiad_session_instance, login_dct, ok )

    def register_new_user( self, illiad_session_instance, user_dct ):
        """ Registers new user.
            Called by check_illiad() """
        try:
            ok = False
            illiad_profile = self._make_profile( user_dct )
            reg_response_dct = illiad_session_instance.register_user( illiad_profile )
            log.info( 'illiad reg_response_dct, ```{}```'.format(pprint.pformat(reg_response_dct)) )
            if reg_response_dct['status'] == 'Registered':
                ok = True
        except Exception as e:
            log.error( 'Exception on new user registration, ```{}```'.format(unicode(repr(e))) )
            ok = False
        log.debug( 'ok, `{}`'.format(ok) )
        return ok

    def _make_profile( self, user_dct ):
        """ Builds illiad_profile dct.
            Called by register_new_user() """
        illiad_profile = {
            'first_name': user_dct['name_first'],
            'last_name': user_dct['name_last'],
            'email': user_dct['email'],
            'status': user_dct['brown_type'],
            'phone': user_dct['phone'],
            'department': user_dct['department'] }
        log.info( 'illiad_profile, {}'.format(pprint.pformat(illiad_profile) ) )
        return illiad_profile

    def logout_user( self, illiad_session_instance ):
        """ Logs out user & logs any errors.
            Called by check_illiad() """
        try:
            illiad_session_instance.logout()
            log.debug( 'illiad logout successful' )
        except Exception as e:
            log.error( 'illiad logout exception, ```%s```' % unicode(repr(e)) )
        return
