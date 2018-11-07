
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
        self.assertEqual( '/borrow/shib_logout/', redirect_url )
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

    def test_make_item_dct__good_data(self):
        """ Good data should return good dct. """
        bib_dct = { 'title': 'the_title', 'isbn': '9781439867976'}
        querystring = 'id=doi:10.1201/b12738-10&sid=crc&iuid=2210&date=2012&pub=Chapman+and+Hall/CRC&aulast=Der&atitle=Logistic+Regression&genre=book&isbn=9781439867976&title=Applied+Medical+Statistics+Using+SAS&btitle=Applied+Medical+Statistics+Using+SAS'
        expected = {
            u'isbn': u'9781439867976',
            u'sfxurl': u'http://rl3tp7zf5x.search.serialssolutions.com/?id=doi:10.1201/b12738-10&sid=crc&iuid=2210&date=2012&pub=Chapman+and+Hall/CRC&aulast=Der&atitle=Logistic+Regression&genre=book&isbn=9781439867976&title=Applied+Medical+Statistics+Using+SAS&btitle=Applied+Medical+Statistics+Using+SAS',
            u'title': u'the_title',
            u'volumes': u'',
            u'wc_accession': 0 }
        self.assertEqual(
            expected, self.helper._make_item_dct(bib_dct,querystring) )

    def test_make_item_dct__bad_isbn(self):
        """ ISBN with hyphens should return cleaned isbn field. """
        bib_dct = { 'title': 'the_title', 'isbn': '978-1-4398-6797-6'}
        querystring = 'id=doi:10.1201/b12738-10&sid=crc&iuid=2210&date=2012&pub=Chapman+and+Hall/CRC&aulast=Der&atitle=Logistic+Regression&genre=book&isbn=978-1-4398-6797-6&title=Applied+Medical+Statistics+Using+SAS&btitle=Applied+Medical+Statistics+Using+SAS'
        expected = {
            u'isbn': u'9781439867976',
            u'sfxurl': u'http://rl3tp7zf5x.search.serialssolutions.com/?id=doi:10.1201/b12738-10&sid=crc&iuid=2210&date=2012&pub=Chapman+and+Hall/CRC&aulast=Der&atitle=Logistic+Regression&genre=book&isbn=978-1-4398-6797-6&title=Applied+Medical+Statistics+Using+SAS&btitle=Applied+Medical+Statistics+Using+SAS',
            u'title': u'the_title',
            u'volumes': u'',
            u'wc_accession': 0 }
        self.assertEqual(
            expected, self.helper._make_item_dct(bib_dct,querystring) )

    def test_make_item_dct_long_title(self):
        """ Checks that too-long title is truncated. """
        bib_dct = { u'title': u'z' * 256, u'isbn': u'978-1-4398-6797-6'}
        querystring = u'id=doi:10.1201/b12738-10&sid=crc&iuid=2210&date=2012&pub=Chapman+and+Hall/CRC&aulast=Der&atitle=Logistic+Regression&genre=book&isbn=978-1-4398-6797-6&title=Applied+Medical+Statistics+Using+SAS&btitle=Applied+Medical+Statistics+Using+SAS'
        rslt_dct = self.helper._make_item_dct(bib_dct,querystring)
        self.assertEqual(
            254, len(rslt_dct['title']) )

    # end ProcessHelperTest()
