
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
from django.test import TestCase
from django.utils.encoding import iri_to_uri
from delivery.classes.availability_helper import AvailabilityViewHelper, JosiahAvailabilityChecker


log = logging.getLogger('access')


class AvailabilityViewHelperTest(TestCase):
    """ Checks AvailabilityViewHelper()
        Not going to test save_to_easyborrow() with good data to avoid executing real request. """

    def setUp(self):
        self.helper = AvailabilityViewHelper()

    def test_build_simple_bib_dct(self):
        """ Should return minimal info. """
        querystring = 'isbn=foo'
        bib_dct = self.helper.build_bib_dct( querystring )
        self.assertEqual( ['_openurl', 'identifier', 'title', 'type'], sorted(bib_dct.keys()) )
        self.assertEqual( [{'type': 'isbn', 'id': 'foo'}], bib_dct['identifier'] )

    def test_build_bib_dct__handle_unicode_in_unicode_string(self):
        """ Should handle unicode-name in unicode string. """
        querystring_8 = b'sid=FirstSearch%3AWorldCat&genre=book&title=Zen&date=1978&aulast=Yoshioka&aufirst=Tōichi&id=doi%3A&pid=6104671%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E6104671%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F6104671&rft.aulast=Yoshioka&rft.aufirst=Tōichi&rft.btitle=Zen&rft.date=1978&rft.place=Osaka++Japan&rft.pub=Hoikusha&rft.edition=1st+ed.&rft.genre=book'
        self.assertEqual( str, type(querystring_8) )
        querystring_encoded_8 = iri_to_uri( querystring_8 )  # b'aufirst=T%C5%8Dichi'
        self.assertEqual( str, type(querystring_encoded_8) )
        querystring_encoded_u = querystring_encoded_8.decode( 'utf-8' )
        self.assertEqual( unicode, type(querystring_encoded_u) )
        bib_dct = self.helper.build_bib_dct( querystring_encoded_u )
        self.assertEqual( ['_openurl', '_rfr', 'author', 'identifier', 'place_of_publication', 'publisher', 'title', 'type', 'year'], sorted(bib_dct.keys()) )
        self.assertEqual( 'T\u014dichi', bib_dct['author'][0]['firstname'] )

    # end AvailabilityViewHelperTest()


class AvailabilityCheckerTest(TestCase):
    """ Checks JosiahAvailabilityChecker() """

    def setUp(self):
        self.checker = JosiahAvailabilityChecker()

    def test_check_josiah_availability__no_oclcnum(self):
        """ Should return holdings for both isbn check and oclc check. """
        isbn = '9788934900894'
        oclc_num = ''
        self.assertEqual(
            [],
            self.checker.check_josiah_availability( isbn, oclc_num )
            )

    def test_check_josiah_availability__holdings_returned(self):
        """ Should return holdings for both isbn check and oclc check. """
        isbn = '9780688002305'
        oclc_num = '673595'
        self.assertEqual(
            [ {'status': 'AVAILABLE', 'callnumber': 'CT275.P648 A33  c.4', 'location': 'ROCK'} ],
            self.checker.check_josiah_availability( isbn, oclc_num )
            )

    # end AvailabilityCheckerTest()

# querystring = 'sid=FirstSearch%3AWorldCat&genre=book&title=Zen&date=1978&aulast=Yoshioka&aufirst=T%C5%8Dichi&id=doi%3A&pid=6104671%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E6104671%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F6104671&rft.aulast=Yoshioka&rft.aufirst=T%C5%8Dichi&rft.btitle=Zen&rft.date=1978&rft.place=Osaka++Japan&rft.pub=Hoikusha&rft.edition=1st+ed.&rft.genre=book'
