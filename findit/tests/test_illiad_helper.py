import json, logging, pprint
from urllib.parse import urlparse, parse_qs

from findit.classes.illiad_helper import IlliadUrlBuilder
from django.test import TestCase


log = logging.getLogger('access')
TestCase.maxDiff = None


class IlliadUrlBuilderTest( TestCase ):
    """ Checks IlliadUrlBuilder() functions. """

    def setUp(self):
        self.builder = IlliadUrlBuilder()
        self.scheme = 'dummy_scheme'
        self.host = 'dummy_host'
        self.permalink = 'dummy_permalink'

    def test_make_illiad_url( self ):
        """ Checks that initial pubmed querystring is transformed properly.
            Initial querystring: `sid=Entrez:PubMed&id=pmid:7623169` """
        initial_querystring = 'pmid=18496984&sid=Entrez:PubMed'
        returned_illiad_url = self.builder.make_illiad_url( initial_querystring, self.scheme, self.host, self.permalink )

        print( f'returned_illiad_url, ```{returned_illiad_url}```' )

        parse_obj = urlparse( returned_illiad_url )
        querystring = parse_obj.query
        print( f'querystring, ```{querystring}```' )
        param_dct = parse_qs( querystring )
        print( f'param_dct, ```{pprint.pformat(param_dct)}```' )

        self.assertEqual(
            ['article'], param_dct['rft.genre'],
            )

        self.assertEqual(
            ['article'], param_dct['rft.genre'],
            )
