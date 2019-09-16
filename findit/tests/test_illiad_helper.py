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
        # self.scheme = 'dummy_scheme'
        # self.host = 'dummy_host'
        # self.permalink = 'dummy_permalink'

    def test_enhance_citation(self):
        """ Checks that poor bib-dct data is enhanced when possible. """
        querystring = 'rft.creator=Yu%2C+Xingfeng&rft.source=Effectiveness+of+a+Nurse-Led+Integrative+Health+and+Wellness+%28NIHaW%29+Programme+on+Behavioural%2C+Psychosocial+and+Biomedical+Outcomes+among+Individuals+with+Newly+Diagnosed+Type+2+Diabetes%3A+A+Randomised+Controlled+Trial&rft.date=2018-01-01&rft.creatorFirst=Xingfeng&rft.creatorLast=Yu&rft.isbn=9780438852358&url_ver=Z39.88-2004&version=1.0&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.genre=article&rfr_id=info%3Asid%2FProQuest+Dissertations+%26+Theses+Global'
        initial_bib_dct = {'_openurl': 'ctx_ver=Z39.88-2004&rft_val_fmt=info%3Aofi/fmt%3Akev%3Amtx%3Ajournal&rft.atitle=Unknown&rft.genre=article&rfr_id=info%3Asid/info%3Asid/ProQuest+Dissertations+%26+Theses+Global&rft.date=2018&rft.isbn=9780438852358',
             '_rfr': 'info:sid/ProQuest Dissertations & Theses Global',
             '_valid': False,
             'identifier': [{'id': '9780438852358', 'type': 'isbn'}],
             'journal': {'name': 'Not provided'},
             'pages': '? - ?',
             'title': 'Unknown',
             'type': 'article',
             'year': '2018'}
        returned_bib_dct = self.builder.enhance_citation( initial_bib_dct, querystring )
        print( f'returned_bib_dct, ```{pprint.pformat(returned_bib_dct)}```' )
        self.assertEqual(
            '(?) Yu, Xingfeng', returned_bib_dct['rft.au'] )
        self.assertEqual(
            '(?) Effectiveness of a Nurse-Led Integrative Health and Wellness (NIHaW) Programme on Behavioural, Psychosocial and Biomedical Outcomes among Individuals with Newly Diagnosed Type 2 Diabetes: A Randomised Controlled Trial',
            returned_bib_dct['rft.atitle'] )
        self.assertEqual(
            '(?) (perhaps listed article title is journal title)',
            returned_bib_dct['rft.jtitle'] )
