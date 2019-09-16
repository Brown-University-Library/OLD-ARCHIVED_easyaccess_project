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
        initial_querystring = 'rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/info:sid/&rft.issue=3&rft_id=info:pmid/7623169&rft.volume=9&rft.atitle=Acute+posterior+fracture+dislocations+of+the+shoulder+treated+with+the+Neer+modification+of+the+McLaughlin+procedure.&ctx_ver=Z39.88-2004&rft.genre=article'
        returned_illiad_url = self.builder.make_illiad_url( initial_querystring, self.scheme, self.host, self.permalink )

        print( f'returned_illiad_url, ```{returned_illiad_url}```' )
        parse_obj = urlparse( returned_illiad_url )
        querystring = parse_obj.query
        print( f'querystring, ```{querystring}```' )
        maybe_dct = parse_qs( querystring )
        print( f'maybe_dct, ```{pprint.pformat(maybe_dct)}```' )



        self.assertEqual(
            2,
            returned_illiad_url
            )
