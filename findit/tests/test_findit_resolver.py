# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint

from django.http import QueryDict
from django.test import TestCase

from delivery.models import Resource
from findit.classes.findit_resolver_helper import FinditResolver
from shorturls import baseconv


log = logging.getLogger('access')
TestCase.maxDiff = None


class FinditResolverTest( TestCase ):
    """ Checks FinditResolver() functions. """

    def setUp(self):
        self.resolver = FinditResolver()
        self.qdct = QueryDict( '', mutable=True )

    def test_check_direct_link__none( self ):
        """ No direct link should return False. """
        sersol_dct = {
            u'dbDate': None,
            u'diagnostics': [ {
                u'details': u'Not enough metadata supplied. We require a title or valid DOI, PMID, or ISSN.',
                u'message': u'Not enough metadata supplied',
                u'uri': u'sersol/diagnostics/8'} ],
            u'echoedQuery': {
                u'library': {u'id': None, u'name': None},
                u'queryString': u'version=1.0&url_ver=Z39.88-2004&isbn=123',
                u'timeStamp': u'2016-03-24T15:22:31' },
            u'results': [],
            u'version': u'1.0'
            }
        self.assertEqual(
            False,  self.resolver.check_direct_link( sersol_dct )
            )
        self.assertEqual(
            False,  self.resolver.direct_link
            )

    def test_check_direct_link__two_available( self ):
        """ Multiple direct links should return True, and set the the direct_link attribute the first article url. """
        sersol_dct = {
            u'dbDate': None,
            u'diagnostics': [ {
                u'details': u'Not enough metadata supplied. We require a title or valid DOI, PMID, or ISSN.',
                u'message': u'Not enough metadata supplied',
                u'uri': u'sersol/diagnostics/8'} ],
            u'echoedQuery': {
                u'library': {u'id': None, u'name': None},
                u'queryString': u'version=1.0&url_ver=Z39.88-2004&isbn=123',
                u'timeStamp': u'2016-03-24T15:22:31' },
            u'results': [ {
                u'linkGroups': [
                        {
                            u'holdingData': {
                                u'databaseId': u'WIK',
                                u'databaseName': u'Wiley-Blackwell Science, Technology and Medicine Collection',
                                u'providerId': u'PRVWIB',
                                u'providerName': u'Wiley-Blackwell',
                                u'startDate': u'1969-01-01'},
                            u'type': u'holding',
                            u'url': {
                                u'article': u'https://login.revproxy.brown.edu/login?url=http://doi.wiley.com/10.1111/j.1095-8312.2011.01617.x',
                                u'issue': u'https://login.revproxy.brown.edu/login?url=http://onlinelibrary.wiley.com/resolve/openurl?genre=issue&eissn=1095-8312&volume=102&issue=4',
                                u'journal': u'https://login.revproxy.brown.edu/login?url=http://onlinelibrary.wiley.com/journal/10.1111/(ISSN)1095-8312',
                                u'source': u'https://login.revproxy.brown.edu/login?url=http://onlinelibrary.wiley.com.revproxy.brown.edu/journal/10.1107/S20532296'}},
                        {
                            u'holdingData': {
                                u'databaseId': u'EAP',
                                u'databaseName': u'Academic Search Premier',
                                u'endDate': u'2015-03-30',
                                u'providerId': u'PRVEBS',
                                u'providerName': u'EBSCOhost',
                                u'startDate': u'2003-01-01'},
                            u'type': u'holding',
                            u'url': {
                                u'article': u'https://login.revproxy.brown.edu/login?url=http://openurl.ebscohost.com/linksvc/linking.aspx?genre=article&issn=0024-4066&date=2011&volume=102&issue=4&spage=715&atitle=Phylogeny+and+divergence+time+of+island+tiger+beetles+of+the+genus+Cylindera+in+East+Asia+PHYLOGENY+OF+TIGER+BEETLES+IN+EAST+ASIA&aulast=SOTA&aufirst=TEIJI',
                                u'journal': u'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/direct.asp?db=aph&jid=JT0&scope=site',
                                u'source': u'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/direct.asp?db=aph'}}
                        ]
                    }
                ],
            u'version': u'1.0'
            }
        self.assertEqual(
            True,  self.resolver.check_direct_link( sersol_dct )
            )
        self.assertEqual(
            'https://login.revproxy.brown.edu/login?url=http://doi.wiley.com/10.1111/j.1095-8312.2011.01617.x',
            self.resolver.direct_link
            )

    def test_check_ebook_no(self):
        """ Checks for proper response when _no_ ebook is found. """
        sersol_dct = {
            u'dbDate': None,
            u'diagnostics': [ {
                u'details': u'Not enough metadata supplied. We require a title or valid DOI, PMID, or ISSN.',
                u'message': u'Not enough metadata supplied',
                u'uri': u'sersol/diagnostics/8'} ],
            u'echoedQuery': {
                u'library': {u'id': None, u'name': None},
                u'queryString': u'version=1.0&url_ver=Z39.88-2004&isbn=123',
                u'timeStamp': u'2016-03-24T15:22:31' },
            u'results': [],
            u'version': u'1.0'
            }
        self.assertEqual(
            ( False, u'', u'') ,  # ( ebook_exists, label, url )
            self.resolver.check_ebook( sersol_dct )
            )

    def test_check_ebook_yes(self):
        """ Checks for proper response when ebook _is_ found. """
        sersol_dct = {
            u'dbDate': u'2016-03-24',
            u'echoedQuery': {
                u'library': {u'id': u'RL3TP7ZF5X', u'name': u'Brown University'},
                u'queryString': u'version=1.0&url_ver=Z39.88-2004&sid=FirstSearch%3AWorldCat&genre=book&title=Zen&date=1978&aulast=Yoshioka&aufirst=T%C5%8Dichi&id=doi%3A&pid=6104671%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E6104671%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F6104671&rft.aulast=Yoshioka&rft.aufirst=T%C5%8Dichi&rft.btitle=Zen&rft.date=1978&rft.place=Osaka++Japan&rft.pub=Hoikusha&rft.edition=1st+ed.&rft.genre=book',
                u'timeStamp': u'2016-03-24T15:32:03' },
            u'results': [ {
                u'citation': {
                    u'creator': u'Yoshioka, T\u014dichi',
                    u'creatorFirst': u'T\u014dichi',
                    u'creatorLast': u'Yoshioka',
                    u'date': u'1978',
                    u'publicationPlace': u'Osaka  Japan',
                    u'publisher': u'Hoikusha',
                    u'source': u'Zen : the religion of the samurai : a study of Zen philosophy and discipline in China and Japan',
                    u'title': u'Zen' },
                u'format': u'book',
                u'linkGroups': [ {
                    u'holdingData': {
                        u'databaseId': u'-VX',
                        u'databaseName': u'eBook Academic Subscription Collection - North America',
                        u'providerId': u'PRVEBS',
                        u'providerName': u'EBSCOhost' },
                    u'type': u'holding',
                    u'url': {
                        u'journal': u'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/login.aspx?direct=true&scope=site&db=e000xna&AN=313762',
                        u'source': u'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/login.aspx?authtype=ip,uid&profile=ehost&defaultdb=e000xna' }
                    } ]
                } ],
            u'version': u'1.0'
            }
        self.assertEqual(
            ## ( ebook_exists, label, url )
            (True, u'eBook Academic Subscription Collection - North America', u'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/login.aspx?direct=true&scope=site&db=e000xna&AN=313762'),
            self.resolver.check_ebook( sersol_dct )
            )

    # end class FinditResolverTest
