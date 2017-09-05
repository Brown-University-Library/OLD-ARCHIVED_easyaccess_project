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

    ########################################
    ## check_double_encoded_querystring() ##

    def test__check_double_encoded_querystring__good_string(self):
        """ For good string, the bad-check sould be false. """
        s = 'ctx_ver=Z39.88-2004&ctx_enc=info%3Aofi%2Fenc%3AUTF-8&rfr_id=info%3Asid%2Fsummon.serialssolutions.com&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.genre=article&rft.atitle=Finance-dominated+capitalism+and+re-distribution+of+income%3A+a+Kaleckian+perspective&rft.jtitle=Cambridge+Journal+of+Economics&rft.au=Hein%2C+E&rft.date=2015-05-01&rft.issn=0309-166X&rft.eissn=1464-3545&rft.volume=39&rft.issue=3&rft.spage=907&rft.epage=934&rft_id=info:doi/10.1093%2Fcje%2Fbet038&rft.externalDBID=n%2Fa&rft.externalDocID=10_1093_cje_bet038'
        self.assertEqual(
            False,
            self.resolver.check_double_encoded_querystring( s )
            )
        self.assertEqual(
            '',
            self.resolver.redirect_url
            )

    def test__check_double_encoded_querystring__double_encoded_string(self):
        """ For double-encoded string, the bad-check sould be true. """
        s = 'ctx_ver=Z39.88-2004&ctx_enc=info%253Aofi%252Fenc%253AUTF-8&rfr_id=info%253Asid%252Fsummon.serialssolutions.com&rft_val_fmt=info%253Aofi%252Ffmt%253Akev%253Amtx%253Ajournal&rft.genre=article&rft.atitle=Finance-dominated+capitalism+and+re-distribution+of+income%253A+a+Kaleckian+perspective&rft.jtitle=Cambridge+Journal+of+Economics&rft.au=Hein%252C+E&rft.date=2015-05-01&rft.issn=0309-166X&rft.eissn=1464-3545&rft.volume=39&rft.issue=3&rft.spage=907&rft.epage=934&rft_id=info:doi/10.1093%252Fcje%252Fbet038&rft.externalDBID=n%252Fa&rft.externalDocID=10_1093_cje_bet038'
        self.assertEqual(
            True,
            self.resolver.check_double_encoded_querystring( s )
            )
        self.assertEqual(
            '/find/?ctx_ver=Z39.88-2004&ctx_enc=info%3Aofi%2Fenc%3AUTF-8&rfr_id=info%3Asid%2Fsummon.serialssolutions.com&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.genre=article&rft.atitle=Finance-dominated+capitalism+and+re-distribution+of+income%3A+a+Kaleckian+perspective&rft.jtitle=Cambridge+Journal+of+Economics&rft.au=Hein%2C+E&rft.date=2015-05-01&rft.issn=0309-166X&rft.eissn=1464-3545&rft.volume=39&rft.issue=3&rft.spage=907&rft.epage=934&rft_id=info:doi/10.1093%2Fcje%2Fbet038&rft.externalDBID=n%2Fa&rft.externalDocID=10_1093_cje_bet038',
            self.resolver.redirect_url
            )

    def test__check_double_encoded_querystring__non_double_encoded_with_embedded_25(self):
        """ For non double-encoded string with an embedded 25, the string can return true, but should be handled fine. """
        s = 'ctx_ver=Z39.88-2004&ctx_enc=info%3Aofi%2Fenc%3AUTF-8&rfr_id=info%3Asid%2Fsummon.serialssolutions.com&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.genre=article&rft.atitle=Examination+of+breakdown+stress+in+creep+by+viscous+glide+in+Al–5·5+at.-%25Mg+solid+solution+alloy+at+high+stress+levels&rft.jtitle=Materials+Science+and+Technology&rft.au=Graiss%2C+G&rft.au=El-Rehim%2C+A.+F.+Abd&rft.date=2007-10-01&rft.issn=0267-0836&rft.eissn=1743-2847&rft.volume=23&rft.issue=10&rft.spage=1144&rft.epage=1148&rft_id=info:doi/10.1179%2F174328407X226545&rft.externalDBID=n%2Fa&rft.externalDocID=10_1179_174328407X226545'
        self.assertEqual(
            True,
            self.resolver.check_double_encoded_querystring( s )
            )
        self.assertEqual(
            '/find/?ctx_ver=Z39.88-2004&ctx_enc=info:ofi/enc:UTF-8&rfr_id=info:sid/summon.serialssolutions.com&rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rft.genre=article&rft.atitle=Examination+of+breakdown+stress+in+creep+by+viscous+glide+in+Al\u20135\xb75+at.-%Mg+solid+solution+alloy+at+high+stress+levels&rft.jtitle=Materials+Science+and+Technology&rft.au=Graiss,+G&rft.au=El-Rehim,+A.+F.+Abd&rft.date=2007-10-01&rft.issn=0267-0836&rft.eissn=1743-2847&rft.volume=23&rft.issue=10&rft.spage=1144&rft.epage=1148&rft_id=info:doi/10.1179/174328407X226545&rft.externalDBID=n/a&rft.externalDocID=10_1179_174328407X226545',
            self.resolver.redirect_url
            )

    #########################
    ## check_direct_link() ##

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

    ###################
    ## check_ebook() ##

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




    ######################################################################
    ## add add_eds_fulltext_url()

    def test_prep_eds_fulltext_url__encoded_url_found(self):
        """ Checks extract of eds url from querystring when present. """
        querystring = 'genre=article&issn=03515796&title=International%20review%20of%20the%20aesthetics%20and%20sociology%20of%20music&volume=10&issue=1&date=19790601&atitle=The%20Orpheon%20societies%3A%20%27Music%20for%20the%20workers%27%20in%20Second-Empire%20France&spage=47&pages=&sid=EBSCO:RILM%20Abstracts%20of%20Music%20Literature%20%281967%20to%20Present%20only%29&aulast=Fulcher,%20Jane%20F.&ebscoperma_link=http%3A%2F%2Fsearch.ebscohost.com%2Flogin.aspx%3Fdirect%3Dtrue%26site%3Deds-live%26scope%3Dsite%26db%3Drih%26AN%3DA406989'
        self.assertEqual(
            'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/login.aspx?direct=true&site=eds-live&scope=site&db=rih&AN=A406989',
            self.resolver.prep_eds_fulltext_url( querystring )
            )

    def test_prep_eds_fulltext_url__url_found_but_not_encoded(self):
        """ Checks extract of eds url from querystring when present but not encoded. """
        querystring = 'genre=article&issn=03515796&title=International%20review%20of%20the%20aesthetics%20and%20sociology%20of%20music&volume=10&issue=1&date=19790601&atitle=The%20Orpheon%20societies%3A%20%27Music%20for%20the%20workers%27%20in%20Second-Empire%20France&spage=47&pages=&sid=EBSCO:RILM%20Abstracts%20of%20Music%20Literature%20%281967%20to%20Present%20only%29&aulast=Fulcher,%20Jane%20F.&ebscoperma_link=http://search.ebscohost.com/login.aspx?direct=true&site=eds-live&scope=site&db=rih&AN=A406989'
        self.assertEqual(
            None,
            self.resolver.prep_eds_fulltext_url( querystring )
            )

    def test_prep_eds_fulltext_url__no_url_found(self):
        """ Checks extract of eds url from querystring when _not_ present. """
        querystring = 'genre=article&issn=03515796&title=International%20review%20of%20the%20aesthetics%20and%20sociology%20of%20music&volume=10&issue=1&date=19790601&atitle=The%20Orpheon%20societies%3A%20%27Music%20for%20the%20workers%27%20in%20Second-Empire%20France&spage=47&pages=&sid=EBSCO:RILM%20Abstracts%20of%20Music%20Literature%20%281967%20to%20Present%20only%29&aulast=Fulcher,%20Jane%20F.'
        self.assertEqual(
            None,
            self.resolver.prep_eds_fulltext_url( querystring )
            )

    ######################################################################
    ## add add_eds_fulltext_url()

    def test_add_eds_fulltext_url__360_direct_links_exist(self):
        """ Checks addition of eds url when 360Link direct-links are found. """
        fulltext_url = 'https://foo/'
        initial_sersol_dct = {
            u'dbDate': None,
            u'diagnostics': [],
            u'echoedQuery': {},
            u'results': [
                {
                    'linkGroups': [
                        {
                        'citation': {},
                        'holdingData': {},
                        'etc': '...'
                        },
                    ]  # there can be more than one set of linkGroups
                },
                {
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
                            u'source': u'https://login.revproxy.brown.edu/login?url=http://onlinelibrary.wiley.com.revproxy.brown.edu/journal/10.1107/S20532296'}
                    },
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
                            u'source': u'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/direct.asp?db=aph'}
                    }
                ]
                }
            ],
            u'version': u'1.0'
            }
        expected_sersol_dct = {
            u'dbDate': None,
            u'diagnostics': [],
            u'echoedQuery': {},
            u'results': [
                {
                    'linkGroups': [
                        {
                        'citation': {},
                        'holdingData': {},
                        'etc': '...'
                        },
                    ]  # there can be more than one set of linkGroups
                },
                {
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
                            u'source': u'https://login.revproxy.brown.edu/login?url=http://onlinelibrary.wiley.com.revproxy.brown.edu/journal/10.1107/S20532296'}
                    },
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
                            u'source': u'https://login.revproxy.brown.edu/login?url=http://search.ebscohost.com/direct.asp?db=aph'}
                    },
                    ]
                },

                {
                    u'linkGroups': [
                    {
                        'holdingData': {
                            'databaseId': '',
                            'databaseName': 'EBSCO Discovery Service',
                            'providerId': '',
                            'providerName': '',
                            'startDate': ''},
                        'type': 'holding',
                        'url': {
                            'article': 'https://login.revproxy.brown.edu/login?url=https://foo/',
                            'issue': '',
                            'journal': '',
                            'source': ''}
                    },
                    ]
                }

            ],  # end `'results': [`
            u'version': u'1.0'
        }
        self.assertEqual( expected_sersol_dct, self.resolver.add_eds_fulltext_url(fulltext_url, initial_sersol_dct) )

        # end def test_add_eds_fulltext_url__360_direct_links_exist()

    def test_add_eds_fulltext_url__NO_360_direct_links_exist(self):
        """ Checks addition of eds url when 360Link direct-links are _not_ found. """
        fulltext_url = 'https://foo/'
        initial_sersol_dct = {
            'dbDate': None,
            'diagnostics': [],
            'echoedQuery': {},
            'results': [ {
                'linkGroups': [],
            } ],
            'version': '1.0'
        }
        expected_sersol_dct = {
            'dbDate': None,
            'diagnostics': [],
            'echoedQuery': {},
            'results': [ {
                'linkGroups': [ {
                    'holdingData': {
                        'databaseId': '',
                        'databaseName': 'EBSCO Discovery Service',
                        'providerId': '',
                        'providerName': '',
                        'startDate': ''},
                    'type': 'holding',
                    'url': {
                        'article': 'https://login.revproxy.brown.edu/login?url=https://foo/',
                        'issue': '',
                        'journal': '',
                        'source': ''}
                }, ]
            } ],
            'version': '1.0'
        }
        self.assertEqual( expected_sersol_dct, self.resolver.add_eds_fulltext_url(fulltext_url, initial_sersol_dct) )

        # end def test_add_eds_fulltext_url__NO_360_direct_links_exist()




    ######################
    ## check_bad_issn() ##

    def test_check_bad_issn(self):
        """ Checks bad-issn handling. """
        sersol_dct = {
            u'dbDate': u'foo',
            u'diagnostics': [{
                u'details': u'Removed issn: edsagr',
                u'message': u'Invalid check sum',
                u'uri': u'sersol/diagnostics/101'
                }],
            u'echoedQuery': {
                u'library': {u'id': u'foo', u'name': u'foo'},
                u'queryString': u'version=1.0&url_ver=Z39.88-2004&version=1.0&url_ver=Z39.88-2004&genre=article&issn=edsagr&title=[Organic%20agriculture%20adoption%20by%20coffe%20producers%20in%20Brasil]%20/%20Ado%c3%a7ao%20da%20agricultura%20organica%20por%20produtores%20de%20caf%c3%a9%20no%20Brasil&volume=&issue=&date=20020101&atitle=%5BOrganic%20agriculture%20adoption%20by%20coffe%20producers%20in%20Brasil%5D%20%2F%20Ado%C3%A7ao%20da%20agricultura%20organica%20por%20produtores%20de%20caf%C3%A9%20no%20Brasil&spage=&pages=&sid=EBSCO:AGRIS&aulast=5.%20Congreso%20de%20la%20Sociedad%20Espa%c3%b1ola%20de%20Agricultura%20Ecol%c3%b3gica,%20Gij%c3%b3n%20(Espa%c3%b1a),%2016-21%20Sep%202002',
                u'timeStamp': u'2017-08-30T07:00:01'},
            u'results': [{
                u'citation': {
                    u'creator': u'5. Congreso de la Sociedad Espa\xf1ola de Agricultura Ecol\xf3gica, Gij\xf3n (Espa\xf1a), 16-21 Sep 2002',
                    u'creatorLast': u'5. Congreso de la Sociedad Espa\xf1ola de Agricultura Ecol\xf3gica, Gij\xf3n (Espa\xf1a), 16-21 Sep 2002',
                    u'date': u'2002-01-01',
                    u'source': u'[Organic agriculture adoption by coffe producers in Brasil] / Ado\xe7ao da agricultura organica por produtores de caf\xe9 no Brasil',
                    u'title': u'[Organic agriculture adoption by coffe producers in Brasil] / Ado\xe7ao da agricultura organica por produtores de caf\xe9 no Brasil'
                    },
               u'format': u'journal',
               u'linkGroups': []
               }],
            u'version': u'1.0'
            }
        ( is_bad_issn, redirect_url ) = self.resolver.check_bad_issn( sersol_dct )
        expected_good_querystring = '/find/?version=1.0&url_ver=Z39.88-2004&version=1.0&url_ver=Z39.88-2004&genre=article&issn=&title=[Organic%20agriculture%20adoption%20by%20coffe%20producers%20in%20Brasil]%20/%20Ado%c3%a7ao%20da%20agricultura%20organica%20por%20produtores%20de%20caf%c3%a9%20no%20Brasil&volume=&issue=&date=20020101&atitle=%5BOrganic%20agriculture%20adoption%20by%20coffe%20producers%20in%20Brasil%5D%20%2F%20Ado%C3%A7ao%20da%20agricultura%20organica%20por%20produtores%20de%20caf%C3%A9%20no%20Brasil&spage=&pages=&sid=EBSCO:AGRIS&aulast=5.%20Congreso%20de%20la%20Sociedad%20Espa%c3%b1ola%20de%20Agricultura%20Ecol%c3%b3gica,%20Gij%c3%b3n%20(Espa%c3%b1a),%2016-21%20Sep%202002'
        self.assertEqual( True, is_bad_issn )
        self.assertEqual( expected_good_querystring, redirect_url )
        ## make good sersol-dct
        sersol_dct['diagnostics'][0]['message'] = ''
        ## rerun tests
        ( is_bad_issn, redirect_url ) = self.resolver.check_bad_issn( sersol_dct )
        self.assertEqual( False, is_bad_issn )
        self.assertEqual( None, redirect_url )

    ###########################
    ## check_pubmed_result() ##

    def test_check_pubmed_result__pubmed_a(self):
        """ Tests one style of pubmed info -- no change needed """
        sersol_dct = {
            'results': [ {
                'citation': {'pmid': 'foo', 'volume': 'bar'},
                'format': 'journal'
                } ]
            }
        self.assertEqual( sersol_dct, self.resolver.check_pubmed_result(sersol_dct) )

    def test_check_pubmed_result__pubmed_b(self):
        """ Tests second style of pubmed info -- format should be `journal` """
        sersol_dct = {
            'results': [ {
                'citation': {'pmid': 'foo', 'volume': 'bar'},
                'format': 'book'
                } ]
            }
        expected_result = {
            u'results': [ {
                'citation': {'pmid': 'foo', 'volume': 'bar'},
                'format': u'journal'}
                ] }
        self.assertEqual( expected_result, self.resolver.check_pubmed_result(sersol_dct) )

    ######################
    ## check_bad_data() ##

    def test_check_bad_data__good_data(self):
        """ Good sersol_dct should return (False, no-redirect-url, no-message) for (check-boolean, redirect-url-string, message) """
        querystring = 'foo=bar'
        sersol_dct = {}
        ( is_bad_data, redirect_url, problem_message ) = self.resolver.check_bad_data( querystring, sersol_dct )
        self.assertEqual( (False, None, None), (is_bad_data, redirect_url, problem_message) )

    def test_check_bad_data__incomplete_data(self):
        """ sersol_dct indicating not-enough-metadata should return (True, a redirect-url, appropriate-message) """
        querystring = 'foo=bar'
        sersol_dct = {
            'diagnostics': [ {
                'message': 'Not enough metadata supplied'
                } ] }
        ( is_bad_data, redirect_url, problem_message ) = self.resolver.check_bad_data( querystring, sersol_dct )
        ( is_bad_data, redirect_url, problem_message ) = self.resolver.check_bad_data( querystring, sersol_dct )
        self.assertEqual( (True, '/find/citation_form/?foo=bar'), (is_bad_data, redirect_url) )
        self.assertTrue( 'not enough information provided' in problem_message )

    def test_check_bad_data__bad_data(self):
        """ sersol_dct indicating not-enough-metadata should return (True, a redirect-url, appropriate-message) """
        querystring = 'foo=bar'
        sersol_dct = {
            'diagnostics': [ {
                'message': 'Invalid syntax'
                } ] }
        ( is_bad_data, redirect_url, problem_message ) = self.resolver.check_bad_data( querystring, sersol_dct )
        self.assertEqual( (True, '/find/citation_form/?foo=bar'), (is_bad_data, redirect_url) )
        self.assertTrue( 'confirm the information' in problem_message )



    # end class FinditResolverTest
