# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from django.conf import settings
from django.http import QueryDict
from django.test import Client, TestCase
from findit.classes.citation_form_helper import CitationFormDctMaker, CitationFormHelper


log = logging.getLogger('access')
TestCase.maxDiff = None


class CitationFormDctMakerTest( TestCase ):
    """ Checks CitationFormDctMaker() functions. """

    def setUp(self):
        self.form_dct_maker = CitationFormDctMaker()
        self.qdct = QueryDict( '', mutable=True )

    ## make_form_dct() checks ##

    def test_make_form_dct__oclc_value(self):
        """ Checks removal of accessionnumber tags. """
        dct = { 'some_oclc_key': '<accessionnumber>1234</accessionnumber>' }
        self.qdct.update(dct)
        self.assertEqual( {
            u'atitle': u'Unknown',
            u'issue': u'',
            u'issn': u'',
            u'jtitle': u'',
            u'some_oclc_key': u'1234',
            u'volume': u''},
            self.form_dct_maker.make_form_dct( self.qdct )
            )

    def test_make_form_dct__id_and_doi(self):
        """ Checks removal of 'doi' from value. """
        dct = { 'id': 'doi:1234' }
        self.qdct.update(dct)
        self.assertEqual(
            {'volume': '', 'issue': '', 'id': '1234', 'atitle': 'Unknown', u'jtitle': u'', u'issn': u''},
            self.form_dct_maker.make_form_dct( self.qdct )
            )

    def test_make_form_dct__doi_key(self):
        """ Checks conversion of doi-key to id-key. """
        dct = { 'doi': '1234' }
        self.qdct.update(dct)
        self.assertEqual(
            {'atitle': 'Unknown', 'id': '1234', 'issue': '', 'volume': '', u'jtitle': u'', u'issn': u''},
            self.form_dct_maker.make_form_dct( self.qdct )
            )

    def test_make_form_dct__simple_isbn(self):
        """ Checks plain isbn. """
        dct = { 'isbn': '1234' }
        self.qdct.update(dct)
        self.assertEqual(
            {u'btitle': None, u'isbn': u'1234', u'place': None, u'pub': None},
            self.form_dct_maker.make_form_dct( self.qdct )
            )



    def test_make_form_dct__article_openurl(self):
        """ Checks large openurl with issn and doi. """
        bibjson_dct = {
            u'_openurl': u'rft_val_fmt=info%3Aofi/fmt%3Akev%3Amtx%3Ajournal&rfr_id=info%3Asid/info%3Asid/info%3Asid/&rft.issue=3&rft.au=Schwenke%2C+K.+D.&rft.eissn=1611-6070&rft.pages=303+-+EOA&rft_id=info%3Adoi/10.1002/food.19720160319&rft.date=1972&rft.volume=16&rft.atitle=Structure%2C+Function+and+Evolution+in+Proteins.+Brookhaven+Symposia+in+Biology+No.+21%2C+Report+of+Symposium+held+June+3%3F5%2C+1968%2C+BNL+50116+%28C%3F53%29+Volume+I+and+II+of+II%2C+428+Seiten+mit+zahlreichen+Abb.+und+Tab.%2C+Biology+Department%2C+Brookhaven+National+Laboratory%2C+Upton%2C+New+York+1969.+Preis+%28printed+copy%29%3A+3.00+%24&ctx_ver=Z39.88-2004&rft.jtitle=Die+Nahrung&rft.issn=0027-769X&rft.genre=article&rft.spage=303',
            u'_rfr': u'info:sid/info:sid/',
            u'author': [{u'name': u'Schwenke, K. D.'}],
            u'identifier': [
                {u'id': u'doi:10.1002/food.19720160319', u'type': u'doi'},
                {u'id': u'0027-769X', u'type': u'issn'},
                {u'id': u'1611-6070', u'type': u'eissn'}],
            u'issue': u'3',
            u'journal': {u'name': u'Die Nahrung'},
            u'pages': u'303 - EOA',
            u'start_page': u'303',
            u'title': u'Structure, Function and Evolution in Proteins. Brookhaven Symposia in Biology No. 21, Report of Symposium held June 3?5, 1968, BNL 50116 (C?53) Volume I and II of II, 428 Seiten mit zahlreichen Abb. und Tab., Biology Department, Brookhaven National Laboratory, Upton, New York 1969. Preis (printed copy): 3.00 $',
            u'type': u'article',
            u'volume': u'16',
            u'year': u'1972'}
        self.qdct.update( bibjson_dct )
        form_dct = self.form_dct_maker.make_form_dct( self.qdct )
        self.assertEqual( '303-EOA', form_dct['pages'] )
        self.assertEqual( '10.1002/food.19720160319', form_dct['id'] )
        self.assertEqual( '0027-769X', form_dct['issn'] )
        self.assertEqual( {
            u'atitle': u'Structure, Function and Evolution in Proteins. Brookhaven Symposia in Biology No. 21, Report of Symposium held June 3?5, 1968, BNL 50116 (C?53) Volume I and II of II, 428 Seiten mit zahlreichen Abb. und Tab., Biology Department, Brookhaven National Laboratory, Upton, New York 1969. Preis (printed copy): 3.00 $',
            # u'issn': u'doi:10.1002/food.19720160319',
            'id': '10.1002/food.19720160319',
            'issn': '0027-769X',
            u'start_page': u'303',
            u'title': u'Structure, Function and Evolution in Proteins. Brookhaven Symposia in Biology No. 21, Report of Symposium held June 3?5, 1968, BNL 50116 (C?53) Volume I and II of II, 428 Seiten mit zahlreichen Abb. und Tab., Biology Department, Brookhaven National Laboratory, Upton, New York 1969. Preis (printed copy): 3.00 $',
            u'issue': u'3',
            u'journal': {u'name': u'Die Nahrung'},
            u'author': {u'name': u'Schwenke, K. D.'},
            u'year': u'1972',
            u'_openurl': u'rft_val_fmt=info%3Aofi/fmt%3Akev%3Amtx%3Ajournal&rfr_id=info%3Asid/info%3Asid/info%3Asid/&rft.issue=3&rft.au=Schwenke%2C+K.+D.&rft.eissn=1611-6070&rft.pages=303+-+EOA&rft_id=info%3Adoi/10.1002/food.19720160319&rft.date=1972&rft.volume=16&rft.atitle=Structure%2C+Function+and+Evolution+in+Proteins.+Brookhaven+Symposia+in+Biology+No.+21%2C+Report+of+Symposium+held+June+3%3F5%2C+1968%2C+BNL+50116+%28C%3F53%29+Volume+I+and+II+of+II%2C+428+Seiten+mit+zahlreichen+Abb.+und+Tab.%2C+Biology+Department%2C+Brookhaven+National+Laboratory%2C+Upton%2C+New+York+1969.+Preis+%28printed+copy%29%3A+3.00+%24&ctx_ver=Z39.88-2004&rft.jtitle=Die+Nahrung&rft.issn=0027-769X&rft.genre=article&rft.spage=303',
            u'volume': u'16',
            u'au': u'Schwenke, K. D.',
            u'_rfr': u'info:sid/info:sid/',
            u'date': u'1972',
            u'identifier': {u'type': u'doi', u'id': u'doi:10.1002/food.19720160319'},
            u'type': u'article',
            u'pages': u'303-EOA',
            u'jtitle': u'Die Nahrung'},
            self.form_dct_maker.make_form_dct(self.qdct)
            )



    def test_make_form_dct__book_openurl(self):
        """ Checks large openurl with no isbn. """
        dct = {
            'aufirst': 'T\u014dichi',
            'aulast': 'Yoshioka',
            'date': '1978',
            'genre': 'book',
            'id': '',
            'pid': '6104671<fssessid>0</fssessid><edition>1st ed.</edition>',
            'req_dat': '<sessionid>0</sessionid>',
            'rfe_dat': '6104671',
            'rfr_id': 'info:sid/firstsearch.oclc.org:WorldCat',
            'rft.aufirst': 'T\u014dichi',
            'rft.aulast': 'Yoshioka',
            'rft.btitle': 'Zen',
            'rft.date': '1978',
            'rft.edition': '1st ed.',
            'rft.genre': 'book',
            'rft.place': 'Osaka  Japan',
            'rft.pub': 'Hoikusha',
            'rft_id': 'info:oclcnum/6104671',
            'rft_val_fmt': 'info:ofi/fmt:kev:mtx:book',
            'sid': 'FirstSearch:WorldCat',
            'title': 'Zen',
            'url_ver': 'Z39.88-2004'}
        self.qdct.update(dct)
        self.assertEqual(
            {'au': 'Yoshioka, T\u014dichi',
             'aufirst': 'T\u014dichi',
             'aulast': 'Yoshioka',
             'btitle': 'Zen',
             'date': '1978',
             'genre': 'book',
             'id': '',
             'pid': '6104671<fssessid>0</fssessid><edition>1st ed.</edition>',
             'place': 'Osaka  Japan',
             'pub': 'Hoikusha',
             'req_dat': '<sessionid>0</sessionid>',
             'rfe_dat': '6104671',
             'rfr_id': 'info:sid/firstsearch.oclc.org:WorldCat',
             'rft.aufirst': 'T\u014dichi',
             'rft.aulast': 'Yoshioka',
             'rft.btitle': 'Zen',
             'rft.date': '1978',
             'rft.edition': '1st ed.',
             'rft.genre': 'book',
             'rft.place': 'Osaka  Japan',
             'rft.pub': 'Hoikusha',
             'rft_id': 'info:oclcnum/6104671',
             'rft_val_fmt': 'info:ofi/fmt:kev:mtx:book',
             'sid': 'FirstSearch:WorldCat',
             'title': 'Zen',
             'url_ver': 'Z39.88-2004'}, self.form_dct_maker.make_form_dct( self.qdct )
            )

    # def test_make_form_dct__book_openurl(self):
    #     """ Checks large openurl. """
    #     dct = {
    #         'aufirst': 'T\u014dichi',
    #         'aulast': 'Yoshioka',
    #         'date': '1978',
    #         'genre': 'book',
    #         'id': '',
    #         'pid': '6104671<fssessid>0</fssessid><edition>1st ed.</edition>',
    #         'req_dat': '<sessionid>0</sessionid>',
    #         'rfe_dat': '6104671',
    #         'rfr_id': 'info:sid/firstsearch.oclc.org:WorldCat',
    #         'rft.aufirst': 'T\u014dichi',
    #         'rft.aulast': 'Yoshioka',
    #         'rft.btitle': 'Zen',
    #         'rft.date': '1978',
    #         'rft.edition': '1st ed.',
    #         'rft.genre': 'book',
    #         'rft.place': 'Osaka  Japan',
    #         'rft.pub': 'Hoikusha',
    #         'rft_id': 'info:oclcnum/6104671',
    #         'rft_val_fmt': 'info:ofi/fmt:kev:mtx:book',
    #         'sid': 'FirstSearch:WorldCat',
    #         'title': 'Zen',
    #         'url_ver': 'Z39.88-2004'}
    #     self.qdct.update(dct)
    #     self.assertEqual(
    #         {'au': 'Yoshioka, T\u014dichi',
    #          'aufirst': 'T\u014dichi',
    #          'aulast': 'Yoshioka',
    #          'date': '1978',
    #          'genre': 'book',
    #          'id': '',
    #          'pid': '6104671<fssessid>0</fssessid><edition>1st ed.</edition>',
    #          'req_dat': '<sessionid>0</sessionid>',
    #          'rfe_dat': '6104671',
    #          'rfr_id': 'info:sid/firstsearch.oclc.org:WorldCat',
    #          'rft.aufirst': 'T\u014dichi',
    #          'rft.aulast': 'Yoshioka',
    #          'rft.btitle': 'Zen',
    #          'rft.date': '1978',
    #          'rft.edition': '1st ed.',
    #          'rft.genre': 'book',
    #          'rft.place': 'Osaka  Japan',
    #          'rft.pub': 'Hoikusha',
    #          'rft_id': 'info:oclcnum/6104671',
    #          'rft_val_fmt': 'info:ofi/fmt:kev:mtx:book',
    #          'sid': 'FirstSearch:WorldCat',
    #          'title': 'Zen',
    #          'url_ver': 'Z39.88-2004'}, self.helper.make_form_dct( self.qdct )
    #         )

    # end class CitationFormDictMakerTest


class CitationFormHelperTest( TestCase ):
    """ Checks view.citation_form() helper functions. """

    def setUp(self):
        self.helper = CitationFormHelper()

    def test_make_form_type_isbn(self):
        """ Checks form_type determination. """
        citation_dct = { 'isbn': '1234' }
        self.assertEqual(
            'book', self.helper.make_form_type( citation_dct )
            )

    def test_make_form_type_no_isbn(self):
        """ Checks form_type determination. """
        citation_dct = {
            'au': 'Yoshioka, T\u014dichi',
            'aufirst': 'T\u014dichi',
            'aulast': 'Yoshioka',
            'date': '1978',
            'genre': 'book',
            'id': '',
            'pid': '6104671<fssessid>0</fssessid><edition>1st ed.</edition>',
            'req_dat': '<sessionid>0</sessionid>',
            'rfe_dat': '6104671',
            'rfr_id': 'info:sid/firstsearch.oclc.org:WorldCat',
            'rft.aufirst': 'T\u014dichi',
            'rft.aulast': 'Yoshioka',
            'rft.btitle': 'Zen',
            'rft.date': '1978',
            'rft.edition': '1st ed.',
            'rft.genre': 'book',
            'rft.place': 'Osaka  Japan',
            'rft.pub': 'Hoikusha',
            'rft_id': 'info:oclcnum/6104671',
            'rft_val_fmt': 'info:ofi/fmt:kev:mtx:book',
            'sid': 'FirstSearch:WorldCat',
            'title': 'Zen',
            'url_ver': 'Z39.88-2004' }
        self.assertEqual(
            'book', self.helper.make_form_type( citation_dct )
            )

    # end class CitationFormHelperTest


class CitationFormClientTest( TestCase ):
    """ Checks citation form via Client. """

    def setUp(self):
        self.client = Client()

    def test_plain_get(self):
        """ Checks plain form. """
        response = self.client.get( '/find/citation_form/' )  # project root part of url is assumed
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '<input type="radio" name="form" value="article">Article' in response.content.decode('utf-8') )
        for key in ['article_form', 'book_form', 'csrf_token', 'form_type', 'messages', 'problem_link' ]:
            self.assertTrue( key in response.context.keys(), 'key `%s` not found' % key )

    def test_get_isbn_parameter(self):
        """ Checks incorporation of param into form. """
        response = self.client.get( '/find/citation_form/?isbn=9780439339117' )  # project root part of url is assumed
        # print response.content
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '9780439339117' in response.content.decode('utf-8') )
        self.assertEqual( 'book', response.context['form_type'] )
        # pprint.pformat( response.context )
        for key in ['article_form', 'book_form', 'csrf_token', 'form_type', 'messages', 'problem_link' ]:
            self.assertTrue( key in response.context.keys(), 'key `%s` not found' % key )

    def test_get_doi_parameter(self):
        """ Checks incorporation of param into form. """
        response = self.client.get( '/find/citation_form/?doi=12611747' )  # project root part of url is assumed
        # print response.content
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '12611747' in response.content.decode('utf-8') )
        self.assertEqual( 'article', response.context['form_type'] )
        pprint.pformat( response.context )
        for key in ['article_form', 'book_form', 'csrf_token', 'form_type', 'messages', 'problem_link' ]:
            self.assertTrue( key in response.context.keys(), 'key `%s` not found' % key )

    # end class CitationFormClientTest
