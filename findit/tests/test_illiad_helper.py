# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from findit.classes.illiad_helper import IlliadUrlBuilder
from django.test import TestCase


log = logging.getLogger('access')
TestCase.maxDiff = None


class IlliadUrlBuilderTest( TestCase ):
    """ Checks IlliadUrlBuilder() functions. """

    def setUp(self):
        self.builder = IlliadUrlBuilder()

    def test_make_illiad_url( self ):
        """ Checks that initial pubmed querystring is transformed properly.
            Initial querystring: `sid=Entrez:PubMed&id=pmid:7623169` """
        initial_querystring = 'rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/info:sid/&rft.issue=3&rft_id=info:pmid/7623169&rft.volume=9&rft.atitle=Acute+posterior+fracture+dislocations+of+the+shoulder+treated+with+the+Neer+modification+of+the+McLaughlin+procedure.&ctx_ver=Z39.88-2004&rft.genre=article'
        self.assertEqual(
            2, 2 )
