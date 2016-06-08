# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, os, pprint, random
from types import NoneType
from common_classes import settings_common_tests as settings_app
from common_classes.illiad_helper import IlliadHelper
from django.test import Client, TestCase


log = logging.getLogger( 'access' )
TestCase.maxDiff = None


class IlliadHelperTest( TestCase ):
    """ Tests common_classes.illiad_helper.IlliadHelper() """

    def setUp(self):
        self.helper = IlliadHelper()
        self.illiad_session_instance = None

    def test_connect(self):
        """ Connect should instantiate illiad_session_instance object.
            Does not yet contact ILLiad (login does), so object is same whether user is good, new, blocked, or disavowed. """
        ill_username = settings_app.TEST_ILLIAD_GOOD_USERNAME
        ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
        self.illiad_session_instance = illiad_session_instance
        self.assertEqual(
            ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
            sorted(illiad_session_instance.__dict__.keys()) )
        self.assertEqual( False, illiad_session_instance.blocked_patron )
        self.assertEqual( False, illiad_session_instance.registered )
        self.assertEqual( None, illiad_session_instance.session_id )
        self.assertEqual( settings_app.TEST_ILLIAD_GOOD_USERNAME, illiad_session_instance.username )
        self.assertEqual( True, ok )

    def test_login__good_user(self):
        """ Good-user login should show user is authenticated, and is registered. """
        ill_username = settings_app.TEST_ILLIAD_GOOD_USERNAME
        ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
        self.illiad_session_instance = illiad_session_instance
        ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )
        ## instance checks
        self.assertEqual(
            ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
            sorted(illiad_session_instance.__dict__.keys()) )
        self.assertEqual( False, illiad_session_instance.blocked_patron )
        self.assertEqual( True, illiad_session_instance.registered )
        self.assertEqual( 11, len(illiad_session_instance.session_id) )
        self.assertEqual( settings_app.TEST_ILLIAD_GOOD_USERNAME, illiad_session_instance.username )
        ## login_dct checks
        self.assertEqual(
            ['authenticated', 'new_user', 'registered', 'session_id'],
            sorted(login_dct.keys()) )
        self.assertEqual( True, login_dct['authenticated'])
        self.assertEqual( False, login_dct['new_user'])
        self.assertEqual( True, login_dct['registered'])
        self.assertEqual( illiad_session_instance.session_id, login_dct['session_id'])
        ## ok check
        self.assertEqual( True, ok )

    def test_login__blocked_user(self):
        """ Blocked-user login should show user is not authenticated, is registered, and is blocked. """
        ill_username = settings_app.TEST_ILLIAD_BLOCKED_USERNAME
        ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
        self.illiad_session_instance = illiad_session_instance
        ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )
        ## instance checks
        self.assertEqual(
            ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
            sorted(illiad_session_instance.__dict__.keys()) )
        self.assertEqual( True, illiad_session_instance.blocked_patron )
        self.assertEqual( True, illiad_session_instance.registered )
        self.assertEqual( None, illiad_session_instance.session_id )
        self.assertEqual( settings_app.TEST_ILLIAD_BLOCKED_USERNAME, illiad_session_instance.username )
        ## login_dct checks
        self.assertEqual(
            ['authenticated', 'blocked', 'new_user', 'session_id'],
            sorted(login_dct.keys()) )
        self.assertEqual( False, login_dct['authenticated'])
        self.assertEqual( True, login_dct['blocked'])
        self.assertEqual( False, login_dct['new_user'])
        self.assertEqual( None, login_dct['session_id'])
        ## ok check
        self.assertEqual( True, ok )

    def test_login__disavowed_user(self):
        """ Disavowed-user login should just fail. """
        ill_username = settings_app.TEST_ILLIAD_DISAVOWED_USERNAME
        ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
        self.illiad_session_instance = illiad_session_instance
        ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )
        ## instance checks
        self.assertEqual( None, illiad_session_instance )
        ## login_dct checks
        self.assertEqual( None, login_dct )
        ## ok check
        self.assertEqual( False, ok )

    def tearDown(self):
        self.helper.logout_user( self.illiad_session_instance )

    # end class IlliadHelperTest()
