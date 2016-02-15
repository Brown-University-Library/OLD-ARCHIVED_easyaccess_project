# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from django.conf import settings
from django.test import Client, TestCase
from django.utils.log import dictConfig


dictConfig(settings.LOGGING)
log = logging.getLogger('access')


class CitationFormTest( TestCase ):
    """ Checks citation form. """

    def setUp(self):
        self.client = Client()

    def test_plain_get(self):
        """ Checks plain form. """
        response = self.client.get( '/find/citation_form/' )  # project root part of url is assumed
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '<input type="radio" name="form" value="article">Article' in response.content.decode('utf-8') )
        for key in ['article_form', 'book_form', 'csrf_token', 'form_type', 'messages', 'problem_link' ]:
            self.assertTrue( key in response.context.keys(), 'key `%s` not found' % key )

    def test_get_parameter(self):
        """ Checks incorporation of param into form. """
        response = self.client.get( '/find/citation_form/?isbn=9780439339117' )  # project root part of url is assumed
        # print response.content
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '9780439339117' in response.content.decode('utf-8') )
        self.assertEqual( 'book', response.context['form_type'] )
        # pprint.pformat( response.context )
        for key in ['article_form', 'book_form', 'csrf_token', 'form_type', 'messages', 'problem_link' ]:
            self.assertTrue( key in response.context.keys(), 'key `%s` not found' % key )
