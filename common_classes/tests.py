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
        self.assertEqual( settings_app.TEST_ILLIAD_GOOD_USERNAME, illiad_session_instance.username )

    def tearDown(self):
        self.helper.logout_user( self.illiad_session_instance )

    # end class IlliadHelperTest()
