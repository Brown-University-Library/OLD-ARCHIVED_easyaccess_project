# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
from .classes.login_helper import LoginHelper
from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

log = logging.getLogger(__name__)
TestCase.maxDiff = None


class LoginHelper_Test( TestCase ):
    """ Tests classes.LoginHelper() """

    def setUp( self ):
        self.helper = LoginHelper()

    def test__something( self ):
        """ Tests whether referrer is valid. """
        ## empty request should fail
        client = Client()
        session = client.session
        meta_dict = {}
        self.assertEqual(
            False,
            self.helper.check_new_referrer(session, meta_dict) )
        ## good request should return True
        client = Client()
        session = client.session
        session['findit_illiad_check_flag'] = 'good'
        session['findit_illiad_check_enhanced_querystring'] = 'querystring_a'
        meta_dict = { 'QUERY_STRING': 'querystring_a' }
        self.assertEqual(
            True,
            self.helper.check_new_referrer(session, meta_dict) )

    # def test__check_new_referrer( self ):
    #     """ Tests whether referrer is valid. """
    #     ## empty request should fail
    #     session_dict = {}
    #     meta_dict = {}
    #     self.assertEqual(
    #         False,
    #         self.helper.check_new_referrer(session_dict, meta_dict) )
    #     ## good request should return True _and_ update session
    #     session_dict = { 'findit_illiad_check_flag': 'good', 'findit_illiad_check_enhanced_querystring': 'querystring_a' }
    #     meta_dict = { 'QUERY_STRING': 'querystring_a' }
    #     self.assertEqual(
    #         False,
    #         'login_openurl' in session_dict )
    #     self.assertEqual(
    #         True,
    #         self.helper.check_new_referrer(session_dict, meta_dict) )
    #     self.assertEqual(
    #         True,
    #         'login_openurl' in session_dict )
