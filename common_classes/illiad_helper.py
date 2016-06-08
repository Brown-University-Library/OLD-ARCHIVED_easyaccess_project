# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from common_classes import settings_common_tests as settings_app
from illiad.account import IlliadSession


log = logging.getLogger('access')


class IlliadHelper( object ):
    """ Contains helpers for views.process_request() """

    def __init__(self):
        pass

    def check_illiad( self, user_dct ):
        """ Logs user into illiad to check for, and handle, 'newuser' status.
            Returns
            Called by views.process_request() """
        ( illiad_session_instance, ok ) = self.connect( ill_username=user_dct['eppn'].split('@')[0] )
        if ok is False:
            return False
        ( illiad_session_instance, ok ) = self.login( illiad_session_instance )
        if ok is False:
            return False
        ok = illiad_session_instance.registered  # boolean
        if illiad_session_instance.registered is False:
            ok = self.register_new_user( illiad_session_instance, user_dct )
        self.logout_user( login_result_dct['illiad_session_instance'] )
        return ok

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
        illiad_login_dct = illiad_session_instance.login()
        ok = True
        log.debug( 'illiad_login_dct, ```{}```'.format(pprint.pformat(illiad_login_dct)) )
        log.debug( 'illiad_session_instance.__dict__, ```{}```'.format(pprint.pformat(illiad_session_instance.__dict__)) )
        log.debug( 'ok, `{}`'.format(ok) )
        return ( illiad_session_instance, ok )

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
