# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
# from pprint import pprint
from django.conf import settings
from django.utils import unittest
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.client import Client
from django.utils.log import dictConfig

from findit import views
from findit import utils

settings.BUL_LINK_CACHE_TIMEOUT = 0
settings.CACHES = {}

dictConfig(settings.LOGGING)
log = logging.getLogger('access')


#Non-book, non-article item
#http://www.worldcat.org/title/einstein-on-the-beach/oclc/29050194
#coins
#http://generator.ocoins.info/?sitePage=info/journal.html
class PmidResolverTest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    # def test_pmid(self):
    #     request = self.factory.get('?pmid=21221393')
    #     response = views.ResolveView(request=request)
    #     #Call get context data to simulate browser hit.
    #     context = response.get_context_data()
    #     #Verify returned links
    #     names = [link['holdingData']['providerName'] for link in context['link_groups']]
    #     self.assertIn("National Library of Medicine", names)
    #     #Verify citation.
    #     citation = context['citation']
    #     self.assertTrue(citation['source'], 'Canadian family physician')
    #     self.assertTrue(citation['volume'], '38')
    #     self.assertTrue(citation['pmid'], '21221393')
    #     self.assertIn('0008-350X', context['citation']['issn']['print'])

    def test_pmid(self):
        request = self.factory.get('?pmid=21221393')
        # response = views.ResolveView(request=request)
        response = views.base_resolver( request=request )
        log.debug( 'response, ```%s```' % pprint.pformat(response.__dict__) )

        ## Call get context data to simulate browser hit.
        context = response.get_context_data()
        ## Verify returned links
        names = [link['holdingData']['providerName'] for link in context['link_groups']]
        self.assertIn("National Library of Medicine", names)
        #Verify citation.
        citation = context['citation']
        self.assertTrue(citation['source'], 'Canadian family physician')
        self.assertTrue(citation['volume'], '38')
        self.assertTrue(citation['pmid'], '21221393')
        self.assertIn('0008-350X', context['citation']['issn']['print'])


class PrintResolverTest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()
    def test_print_holding(self):
        request = self.factory.get('?rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.spage=80&rft.au=Churchland%2C%20PS&rft.aulast=Churchland&rft.format=journal&rft.date=1983&rft.aufirst=PS&rft.volume=64&rft.eissn=1468-0114&rft.atitle=Consciousness%3A%20The%20transmutation%20of%20a%20concept&rft.jtitle=Pacific%20philosophical%20quarterly&rft.issn=0279-0750&rft.genre=article&url_ver=Z39.88-2004&rfr_id=info:sid/libx%3Abrown')
        response = views.ResolveView(request=request)
        context = response.get_context_data()
        citation = context['citation']
        self.assertTrue(citation['source'], 'Pacific philosophical quarterly')
        self.assertTrue(citation['creatorLast'], 'Churchland')
        self.assertTrue(context['link_groups'][0]['holdingData']['providerName'],
                        'Library Specific Holdings')

class EasyBorrowResolverTest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_pass_to_easy_borrow(self):
        """
        Book requests (like this) should be handed off to easyBorrow.
        """
        g = '?sid=FirstSearch%3AWorldCat&genre=book&isbn=9780394565279&title=The+risk+pool&date=1988&aulast=Russo&aufirst=Richard&id=doi%3A&pid=%3Caccession+number%3E17803510%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E17803510%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F17803510&rft_id=urn%3AISBN%3A9780394565279&rft.aulast=Russo&rft.aufirst=Richard&rft.btitle=The+risk+pool&rft.date=1988&rft.isbn=9780394565279&rft.place=New+York&rft.pub=Random+House&rft.edition=1st+ed.&rft.genre=book&checksum=d6c1576188e0f87ac13f4c4582382b4f&title=Brown University&linktype=openurl&detail=RBN'
        c = Client()
        response = c.get(g)
        self.assertEqual(response.status_code, 302)
        content = str(response)
        self.assertTrue(content.rfind('ezborrow') > -1)
        #also make sure the OCLC number was passed on
        self.assertTrue(content.rfind('17803510') > -1)

    def test_easy_borrow_handoff(self):
        from findit.utils import BulSerSol
        import urlparse
        ourl = '?sid=FirstSearch%3AWorldCat&genre=book&isbn=9780394565279&title=The+risk+pool&date=1988&aulast=Russo&aufirst=Richard&id=doi%3A&pid=%3Caccession+number%3E17803510%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E17803510%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F17803510&rft_id=urn%3AISBN%3A9780394565279&rft.aulast=Russo&rft.aufirst=Richard&rft.btitle=The+risk+pool&rft.date=1988&rft.isbn=9780394565279&rft.place=New+York&rft.pub=Random+House&rft.edition=1st+ed.&rft.genre=book&checksum=d6c1576188e0f87ac13f4c4582382b4f&title=Brown University&linktype=openurl&detail=RBN'
        request = self.factory.get(ourl)
        response = views.ResolveView(request=request)
        sersol = response.get_data()
        #pprint(sersol)
        resolved = BulSerSol(sersol)
        eb = resolved.easy_borrow_query()
        eb_dict = urlparse.parse_qs(eb)
        self.assertTrue(eb_dict['rfe_dat'], '17803510')
        self.assertTrue(eb_dict['isbn'], '9780394565279')
        self.assertTrue(eb_dict['author'], 'Russo, Richard')

class EbookResolverTest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_ebook(self):
        o = '?rft.pub=Yale+University+Press&rft.aulast=Dyson&rft.isbn=9780300110975&rft.isbn=9780300110975&rft.author=Dyson%2C+Stephen+L&rft.btitle=In+pursuit+of+ancient+pasts+%3A+a+history+of+classical+archaeology+in+the+nineteenth+and+twentieth+centuries&rft.btitle=In+pursuit+of+ancient+pasts+%3A+a+history+of+classical+archaeology+in+the+nineteenth+and+twentieth+centuries&rft.aufirst=Stephen&rft.place=New+Haven&rft.date=2006&rft.auinitm=L&url_ver=Z39.88-2004&version=1.0&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&rfe_dat=%3Caccessionnumber%3E70062939%3C%2Faccessionnumber%3E'
        request = self.factory.get(o)
        response = views.ResolveView(request=request)
        context = response.get_context_data()
        citation = context['citation']
        lg = context['link_groups']
        self.assertTrue('In pursuit of ancient pasts : a history of classical archaeology in the nineteenth and twentieth centuries',
                        citation['title'])
        self.assertTrue('Yale University Press',
                        citation['publisher'])
        self.assertTrue('Ebrary Academic Complete Subscription Collection',
                        lg[0]['holdingData']['databaseName'])

class ConferenceReportResolverTest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()
    def test_econference_report(self):
        request = self.factory.get('?id=10.1109/CCECE.2011.6030651')
        response = views.ResolveView(request=request)
        context = response.get_context_data()
        citation = context['citation']
        self.assertTrue('Electrical and Computer Engineering (CCECE), 2011 24th Canadian Conference on', citation['source'])
        self.assertTrue('Islam', citation['creatorLast'])

class PublicationView(unittest.TestCase):

    def test_publication_view_redirect(self):
        ourl = '?sid=FirstSearch%3AWorldCat&genre=journal&issn=0017-811X&eissn=2161-976X&title=Harvard+law+review.&date=1887&id=doi%3A&pid=<accession+number>1751808<%2Faccession+number><fssessid>0<%2Ffssessid>&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&req_dat=<sessionid>0<%2Fsessionid>&rfe_dat=<accessionnumber>1751808<%2Faccessionnumber>&rft_id=info%3Aoclcnum%2F1751808&rft_id=urn%3AISSN%3A0017-811X&rft.jtitle=Harvard+law+review.&rft.issn=0017-811X&rft.eissn=2161-976X&rft.aucorp=Harvard+Law+Review+Publishing+Association.%3BHarvard+Law+Review+Association.&rft.place=Cambridge++Mass.&rft.pub=Harvard+Law+Review+Pub.+Association&rft.genre=journal&checksum=059306b04e1938ee38f852a498bea79e&title=Brown%20University&linktype=openurl&detail=RBN'
        #response = views.Reso
        client = Client()
        response = client.get('/%s' % ourl)
        self.assertEqual(response.status_code, 302)





