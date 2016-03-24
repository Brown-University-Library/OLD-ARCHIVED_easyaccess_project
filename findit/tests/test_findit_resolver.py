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
