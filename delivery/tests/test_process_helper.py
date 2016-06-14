
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
from delivery import app_settings
from delivery.classes.process_helper import ProcessViewHelper
from django.test import TestCase


log = logging.getLogger('access')
log.debug( 'testing123' )


class ProcessHelperTest(TestCase):
    """ Checks ProcessViewHelper()
        Not going to test save_to_easyborrow() with good data to avoid executing real request. """

    def setUp(self):
        self.helper = ProcessViewHelper()

    def test_check_if_authorized__bad_data(self):
        """ Bad data should return False. """
        shib_dct = {}
        ( is_authorized, redirect_url, message ) = self.helper.check_if_authorized(shib_dct)
        self.assertEqual( False, is_authorized )
        self.assertEqual( '/borrow/message/', redirect_url )
        self.assertTrue( 'you are not authorized' in message )

    def test_check_if_authorized__good_data(self):
        """ Good data should return True. """
        shib_dct = { 'member_of': app_settings.REQUIRED_GROUPER_GROUP }
        ( is_authorized, redirect_url, message ) = self.helper.check_if_authorized(shib_dct)
        self.assertEqual( True, is_authorized )
        self.assertEqual( '', redirect_url )
        self.assertEqual( '', message )

    def test_save_to_easyborrow(self):
        """ Bad data should return None. """
        bib_dct = {}
        shib_dct = {}
        querystring = ''
        self.assertEqual( None, self.helper.save_to_easyborrow(shib_dct, bib_dct, querystring) )  # a good save would return the ezb-db-id

    # end ProcessHelperTest()
