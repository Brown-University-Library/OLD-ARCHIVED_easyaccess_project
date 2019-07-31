
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
from delivery.classes.shib_helper import ShibLoginHelper
from django.test import TestCase


log = logging.getLogger('access')
TestCase.maxDiff = None


class ShibLoginHelperTest( TestCase ):
    """ Tests querystring builder called from views.shib_login() """

    def setUp(self):
        self.helper = ShibLoginHelper()

    def test_build_shib_sp_querystring(self):
        """ Checks localdev querystring. """
        bib_dct_json = '{"param_a": "a\\u00e1a"}'  # json version of {'param_a': 'aáa'}
        last_querystring = 'rft.atitle=Stalking the Wild Basenji'
        permalink_url = 'http://domain/aa/bb/shortlink_letters/'
        log_id = 'foo'
        mock_reverse_string = '/foo/borrow/login_handler/'  #  the view will actually send: `reverse('borrow:login_handler_url')`
        self.assertEqual(
            # 'target=%2Feasyaccess%2Fborrow%2Flogin_handler%2F%3Fbib_dct_json%3D%257B%2522param_a%2522%253A%2520%2522a%255Cu00e1a%2522%257D%26last_querystring%3Drft.atitle%253DStalking%2520the%2520Wild%2520Basenji%26permalink_url%3Dhttp%253A%2F%2Fdomain%2Faa%2Fbb%2Fshortlink_letters%2F%26ezlogid%3Dfoo',
            'target=%2Ffoo%2Fborrow%2Flogin_handler%2F%3Fbib_dct_json%3D%257B%2522param_a%2522%253A%2520%2522a%255Cu00e1a%2522%257D%26last_querystring%3Drft.atitle%253DStalking%2520the%2520Wild%2520Basenji%26permalink_url%3Dhttp%253A%2F%2Fdomain%2Faa%2Fbb%2Fshortlink_letters%2F%26ezlogid%3Dfoo',
            self.helper.build_shib_sp_querystring( mock_reverse_string, bib_dct_json, last_querystring, permalink_url, log_id )
        )

    def test_build_localdev_querystring(self):
        """ Checks localdev querystring. """
        bib_dct_json = '{"param_a": "a\\u00e1a"}'  # json version of {'param_a': 'aáa'}
        last_querystring = 'rft.atitle=Stalking the Wild Basenji'
        permalink_url = 'http://domain/aa/bb/shortlink_letters/'
        log_id = 'foo'
        self.assertEqual(
            'bib_dct_json=%7B%22param_a%22%3A%20%22a%5Cu00e1a%22%7D&last_querystring=rft.atitle%3DStalking%20the%20Wild%20Basenji&permalink_url=http%3A//domain/aa/bb/shortlink_letters/&ezlogid=foo',
            self.helper.build_localdev_querystring( bib_dct_json, last_querystring, permalink_url, log_id )
        )

    ## end class ShibLoginHelperTest()
