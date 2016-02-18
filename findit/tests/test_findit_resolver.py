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


class FinditResolverHelperTest( TestCase ):
    """ Checks helper functions. """

    def setUp(self):
        self.helper = FinditResolver()
        self.qdct = QueryDict( '', mutable=True )

    def test_make_permalink__resource_not_found(self):
        """ Checks permalink creation. """
        qstring = 'sid=FirstSearch%3AWorldCat&genre=journal&issn=0017-811X&eissn=2161-976X&title=Harvard+law+review.&date=1887&id=doi%3A&pid=<accession+number>1751808<%2Faccession+number><fssessid>0<%2Ffssessid>&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&req_dat=<sessionid>0<%2Fsessionid>&rfe_dat=<accessionnumber>1751808<%2Faccessionnumber>&rft_id=info%3Aoclcnum%2F1751808&rft_id=urn%3AISSN%3A0017-811X&rft.jtitle=Harvard+law+review.&rft.issn=0017-811X&rft.eissn=2161-976X&rft.aucorp=Harvard+Law+Review+Publishing+Association.%3BHarvard+Law+Review+Association.&rft.place=Cambridge++Mass.&rft.pub=Harvard+Law+Review+Pub.+Association&rft.genre=journal&checksum=059306b04e1938ee38f852a498bea79e&title=Brown%20University&linktype=openurl&detail=RBN'
        qdct = { 'rfr_id': 'info:sid/firstsearch.oclc.org:WorldCat' }
        self.qdct.update( qdct )
        data_dct = self.helper.make_permalink( qdct.get('rfr_id',''), qstring, scheme='https', host='the_host' )
        self.assertEqual(
            'https://the_host/easyaccess/find/permalink/B/', data_dct['permalink'] )
        self.assertEqual(
            'info:sid/firstsearch.oclc.org:WorldCat', data_dct['referrer'] )
        self.assertEqual(
            qstring, data_dct['querystring'] )
        self.assertEqual(
            1, data_dct['resource_id'] )
        self.assertEqual(
            'B', data_dct['permastring'] )
        self.assertEqual(
            1, baseconv.base62.to_decimal('B') )

    def test_make_permalink__resource_found(self):
        """ Checks permalink creation. """
        rsc = Resource()
        rsc.query = 'foo'
        rsc.referrer = 'bar'
        rsc.save()
        good_qstring = 'sid=FirstSearch%3AWorldCat&genre=journal&issn=0017-811X&eissn=2161-976X&title=Harvard+law+review.&date=1887&id=doi%3A&pid=<accession+number>1751808<%2Faccession+number><fssessid>0<%2Ffssessid>&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&req_dat=<sessionid>0<%2Fsessionid>&rfe_dat=<accessionnumber>1751808<%2Faccessionnumber>&rft_id=info%3Aoclcnum%2F1751808&rft_id=urn%3AISSN%3A0017-811X&rft.jtitle=Harvard+law+review.&rft.issn=0017-811X&rft.eissn=2161-976X&rft.aucorp=Harvard+Law+Review+Publishing+Association.%3BHarvard+Law+Review+Association.&rft.place=Cambridge++Mass.&rft.pub=Harvard+Law+Review+Pub.+Association&rft.genre=journal&checksum=059306b04e1938ee38f852a498bea79e&title=Brown%20University&linktype=openurl&detail=RBN'
        good_referrer = 'info:sid/firstsearch.oclc.org:WorldCat'
        rsc2 = Resource()
        rsc2.id = 12345678
        rsc2.query = good_qstring
        rsc2.referrer = good_referrer
        rsc2.save()
        data_dct = self.helper.make_permalink( good_referrer, good_qstring, scheme='https', host='the_host' )
        self.assertEqual(
            'https://the_host/easyaccess/find/permalink/pnfq/', data_dct['permalink'] )
        self.assertEqual(
            'info:sid/firstsearch.oclc.org:WorldCat', data_dct['referrer'] )
        self.assertEqual(
            good_qstring, data_dct['querystring'] )
        self.assertEqual(
            12345678, data_dct['resource_id'] )
        self.assertEqual(
            'pnfq', data_dct['permastring'] )
        self.assertEqual(
            12345678, baseconv.base62.to_decimal('pnfq') )

    # end class FinditResolverHelperTest
