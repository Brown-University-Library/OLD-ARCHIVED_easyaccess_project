# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from django.conf import settings
from django.http import QueryDict
from django.test import Client, TestCase
from django.utils.log import dictConfig
from findit.classes.citation_form_helper import CitationFormHelper


dictConfig(settings.LOGGING)
log = logging.getLogger('access')


class CitationFormHelperTest( TestCase ):
    """ Checks helper functions. """

    def setUp(self):
        self.helper = CitationFormHelper()
        self.qdct = QueryDict( '', mutable=True )

    def test_make_form_dct__oclc_value(self):
        """ Checks removal of accessionnumber tags. """
        dct = { 'some_oclc_key': '<accessionnumber>1234</accessionnumber>' }
        self.qdct.update(dct)
        self.assertEqual(
            { 'some_oclc_key': '1234' }, self.helper.make_form_dct( self.qdct )
            )

    def test_make_form_dct__id_and_doi(self):
        """ Checks removal of 'doi' from value. """
        dct = { 'id': 'doi:1234' }
        self.qdct.update(dct)
        self.assertEqual(
            { 'id': '1234' }, self.helper.make_form_dct( self.qdct )
            )

    def test_make_form_dct__doi_key(self):
        """ Checks conversion of doi-key to id-key. """
        dct = { 'doi': '1234' }
        self.qdct.update(dct)
        self.assertEqual(
            { 'id': '1234' }, self.helper.make_form_dct( self.qdct )
            )

    def test_make_form_dct__isbn(self):
        """ Checks plain isbn. """
        dct = { 'isbn': '1234' }
        self.qdct.update(dct)
        self.assertEqual(
            { 'isbn': '1234' }, self.helper.make_form_dct( self.qdct )
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
        self.assertEqual( True, 'z12611747z' in response.content.decode('utf-8') )
        self.assertEqual( 'article', response.context['form_type'] )
        pprint.pformat( response.context )
        for key in ['article_form', 'book_form', 'csrf_token', 'form_type', 'messages', 'problem_link' ]:
            self.assertTrue( key in response.context.keys(), 'key `%s` not found' % key )
