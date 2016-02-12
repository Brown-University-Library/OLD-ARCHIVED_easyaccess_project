# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from django.conf import settings
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.utils.log import dictConfig
from findit import utils, views

settings.BUL_LINK_CACHE_TIMEOUT = 0
settings.CACHES = {}

dictConfig(settings.LOGGING)
log = logging.getLogger('access')


class IndexPageLinksTest( TestCase ):
    """ Checks example links on index page. """

    def setUp(self):
        self.client = Client()

    def test_index(self):
        """ Checks main index page. """
        response = self.client.get( '/find/' )  # project root part of url is assumed
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '<title>easyAccess - Brown University Library</title>' in response.content )
        self.assertEqual( True, '<h3>easyAccess</h3>' in response.content )
        self.assertEqual( True, 'class="intro">Examples' in response.content )
        self.assertEqual( True, '>Login<' in response.content )

    def test_article_held_electronically(self):
        """ Checks the `Article held electronically.` link """
        response = self.client.get( '/find/?sid=google&auinit=T&aulast=SOTA&atitle=Phylogeny+and+divergence+time+of+island+tiger+beetles+of+the+genus+Cylindera+(Coleoptera:+Cicindelidae)+in+East+Asia&id=doi:10.1111/j.1095-8312.2011.01617.x&title=Biological+journal+of+the+Linnean+Society&volume=102&issue=4&date=2011&spage=715&issn=0024-4066' )
        # print 'RESPONSE CONTENT...'; print response.content
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '<title>easyArticle - Brown University Library</title>' in response.content )
        self.assertEqual( True, '<h3>easyArticle</h3>' in response.content )
        self.assertEqual( True, '<h3>Available online</h3>' in response.content )

    def test_article_chapter_held_at_annex(self):
        """ Checks the `Article/Chapter held at Annex.` link """
        from findit.models import PrintTitle
        print_title = PrintTitle(
            key='003776861966', issn='0037-7686', start='1966', end='1992', location='Annex', call_number='BL60.A2 S65' )
        print_title.save()
        response = self.client.get( '/find/?genre=article&issn=00377686&title=Social+Compass&volume=14&issue=5/6&date=19670901&atitle=Religious+knowledge+and+attitudes+in+Mexico+City.&spage=469&pages=469-482&sid=EBSCO:Academic+Search+Premier&aulast=Stryckman,+Paul' )
        content = response.content.decode( 'utf-8' )
        # log.debug( 'response.content, ```%s```' % response.content.decode('utf-8') )
        self.assertEqual( 200, response.status_code )
        self.assertEqual( True, '<title>easyArticle - Brown University Library</title>' in content )
        self.assertEqual( True, '<h3>easyArticle</h3>' in content )
        self.assertEqual( True, '<h3>Available at the library</h3>' in content )
        self.assertEqual( True, '<span class="print-location">Annex</span>' in content )
        self.assertEqual( True, '<span class="print-callnumber">BL60.A2 S65</span>' in content )

    ## end class IndexPageLinksTest


# #Non-book, non-article item
# #http://www.worldcat.org/title/einstein-on-the-beach/oclc/29050194
# #coins
# #http://generator.ocoins.info/?sitePage=info/journal.html
# class PmidResolverTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()

#     # def test_pmid(self):
#     #     request = self.factory.get('?pmid=21221393')
#     #     response = views.ResolveView(request=request)
#     #     #Call get context data to simulate browser hit.
#     #     context = response.get_context_data()
#     #     #Verify returned links
#     #     names = [link['holdingData']['providerName'] for link in context['link_groups']]
#     #     self.assertIn("National Library of Medicine", names)
#     #     #Verify citation.
#     #     citation = context['citation']
#     #     self.assertTrue(citation['source'], 'Canadian family physician')
#     #     self.assertTrue(citation['volume'], '38')
#     #     self.assertTrue(citation['pmid'], '21221393')
#     #     self.assertIn('0008-350X', context['citation']['issn']['print'])

#     def test_pmid(self):
#         request = self.factory.get('?pmid=21221393')
#         # response = views.ResolveView(request=request)
#         response = views.base_resolver( request=request )
#         log.debug( 'response, ```%s```' % pprint.pformat(response.__dict__) )

#         ## Call get context data to simulate browser hit.
#         context = response.get_context_data()
#         ## Verify returned links
#         names = [link['holdingData']['providerName'] for link in context['link_groups']]
#         self.assertIn("National Library of Medicine", names)
#         #Verify citation.
#         citation = context['citation']
#         self.assertTrue(citation['source'], 'Canadian family physician')
#         self.assertTrue(citation['volume'], '38')
#         self.assertTrue(citation['pmid'], '21221393')
#         self.assertIn('0008-350X', context['citation']['issn']['print'])


class PmidResolverTest(TestCase):
    """ Checks non-book, non-article item.
        - http://www.worldcat.org/title/einstein-on-the-beach/oclc/29050194
        - coins -- http://generator.ocoins.info/?sitePage=info/journal.html """

    def test_pmid(self):
        """ Checks non-book, non-article item. """
        url = '/find/?pmid=21221393'
        c = Client()
        response = c.get( url )
        # log.debug( 'response.content, ```%s```' % response.content )
        # log.debug( 'response.context, ```%s```' % pprint.pformat(response.context) )
        # log.debug( 'response.__dict__, ```%s```' % pprint.pformat(response.__dict__) )
        # log.debug( 'dir(response), ```%s```' % pprint.pformat(dir(response)) )
        # log.debug( 'response._headers, ```%s```' % pprint.pformat(response._headers) )
        log.debug( 'response._headers["location"][1], ```%s```' % pprint.pformat(response._headers['location'][1]) )
        redirect_url = response._headers['location'][1]
        self.assertEqual( 'http://brown.summon.serialssolutions.com/2.0.0/link/0/eLv', redirect_url[0:57] )

    # end class PmidResolverTest


class PrintResolverTest(TestCase):

    def test_print_holding(self):
        """ Checks held-book context. """
        url = '/find/?rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.spage=80&rft.au=Churchland%2C%20PS&rft.aulast=Churchland&rft.format=journal&rft.date=1983&rft.aufirst=PS&rft.volume=64&rft.eissn=1468-0114&rft.atitle=Consciousness%3A%20The%20transmutation%20of%20a%20concept&rft.jtitle=Pacific%20philosophical%20quarterly&rft.issn=0279-0750&rft.genre=article&url_ver=Z39.88-2004&rfr_id=info:sid/libx%3Abrown'
        c = Client()
        response = c.get( url, SERVER_NAME='127.0.0.1' )
        # log.debug( 'context.keys(), `%s`' % pprint.pformat( sorted(response.context.keys()) ) )
        citation = response.context['citation']
        link_groups = response.context['link_groups']
        # log.debug( 'citation, `%s`' % pprint.pformat(citation) )
        # log.debug( 'link_groups, `%s`' % pprint.pformat(link_groups) )
        self.assertEqual( 'Pacific philosophical quarterly', citation['source'] )
        self.assertEqual( 'Churchland', citation['creatorLast'] )
        self.assertEqual( 'Library Specific Holdings', link_groups[0]['holdingData']['providerName'] )

    # end class PrintResolverTest


class EasyBorrowResolverTest(TestCase):

    def test_pass_to_easy_borrow(self):
        """ Checks that book request hands off to easyBorrow landing page. """
        url = '/find/?sid=FirstSearch%3AWorldCat&genre=book&isbn=9780394565279&title=The+risk+pool&date=1988&aulast=Russo&aufirst=Richard&id=doi%3A&pid=%3Caccession+number%3E17803510%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E17803510%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F17803510&rft_id=urn%3AISBN%3A9780394565279&rft.aulast=Russo&rft.aufirst=Richard&rft.btitle=The+risk+pool&rft.date=1988&rft.isbn=9780394565279&rft.place=New+York&rft.pub=Random+House&rft.edition=1st+ed.&rft.genre=book&checksum=d6c1576188e0f87ac13f4c4582382b4f&title=Brown University&linktype=openurl&detail=RBN'
        c = Client()
        response = c.get( url, SERVER_NAME='127.0.0.1' )
        self.assertEqual(response.status_code, 302)
        response2 = c.get( url, SERVER_NAME='127.0.0.1', follow=True )
        content = response2.content.decode( 'utf-8' )
        # log.debug( 'type(content), `%s`' % type(content) )
        self.assertTrue( content.rfind('easyBorrow') > -1 )
        self.assertTrue( content.rfind('17803510') > -1 )  # accession number
        ## testing context's bibjson...
        # log.debug( 'context.keys(), `%s`' % pprint.pformat( sorted(response2.context.keys()) ) )
        bibjson_dct = json.loads( response2.context['bibjson'] )
        self.assertEqual( 'Russo, Richard', bibjson_dct['author'][0]['name'] )
        self.assertEqual( '9780394565279', bibjson_dct['identifier'][0]['id'] )
        self.assertEqual( 'isbn', bibjson_dct['identifier'][0]['type'] )
        self.assertEqual( '17803510', bibjson_dct['identifier'][1]['id'] )
        self.assertEqual( 'oclc', bibjson_dct['identifier'][1]['type'] )

    ## end class EasyBorrowResolverTest


# class EbookResolverTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()

#     def test_ebook(self):
#         o = '?rft.pub=Yale+University+Press&rft.aulast=Dyson&rft.isbn=9780300110975&rft.isbn=9780300110975&rft.author=Dyson%2C+Stephen+L&rft.btitle=In+pursuit+of+ancient+pasts+%3A+a+history+of+classical+archaeology+in+the+nineteenth+and+twentieth+centuries&rft.btitle=In+pursuit+of+ancient+pasts+%3A+a+history+of+classical+archaeology+in+the+nineteenth+and+twentieth+centuries&rft.aufirst=Stephen&rft.place=New+Haven&rft.date=2006&rft.auinitm=L&url_ver=Z39.88-2004&version=1.0&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&rfe_dat=%3Caccessionnumber%3E70062939%3C%2Faccessionnumber%3E'
#         request = self.factory.get(o)
#         response = views.ResolveView(request=request)
#         context = response.get_context_data()
#         citation = context['citation']
#         lg = context['link_groups']
#         self.assertTrue('In pursuit of ancient pasts : a history of classical archaeology in the nineteenth and twentieth centuries',
#                         citation['title'])
#         self.assertTrue('Yale University Press',
#                         citation['publisher'])
#         self.assertTrue('Ebrary Academic Complete Subscription Collection',
#                         lg[0]['holdingData']['databaseName'])

class EbookResolverTest(TestCase):

    def test_book_with_ebook_available_redirect(self):
        """ Checks book resolution when an ebook is available.
            Handled as a regular book -- the ebook info is displayed in 'delivery' """
        url = '/find/?rft.pub=Yale+University+Press&rft.aulast=Dyson&rft.isbn=9780300110975&rft.isbn=9780300110975&rft.author=Dyson%2C+Stephen+L&rft.btitle=In+pursuit+of+ancient+pasts+%3A+a+history+of+classical+archaeology+in+the+nineteenth+and+twentieth+centuries&rft.btitle=In+pursuit+of+ancient+pasts+%3A+a+history+of+classical+archaeology+in+the+nineteenth+and+twentieth+centuries&rft.aufirst=Stephen&rft.place=New+Haven&rft.date=2006&rft.auinitm=L&url_ver=Z39.88-2004&version=1.0&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&rfe_dat=%3Caccessionnumber%3E70062939%3C%2Faccessionnumber%3E'
        c = Client()
        response = c.get( url, SERVER_NAME='127.0.0.1' )
        # log.debug( 'response._headers, ```%s```' % pprint.pformat(response._headers) )
        # log.debug( 'response._headers["location"][1], ```%s```' % pprint.pformat(response._headers['location'][1]) )
        redirect_url = response._headers['location'][1]
        self.assertEqual( 'http://127.0.0.1/borrow/?rft.pub=Yale+University+Press', redirect_url[0:54] )

    # end class EbookResolverTest


class ConferenceReportResolverTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
    def test_econference_report(self):
        request = self.factory.get('?id=10.1109/CCECE.2011.6030651')
        response = views.ResolveView(request=request)
        context = response.get_context_data()
        citation = context['citation']
        self.assertTrue('Electrical and Computer Engineering (CCECE), 2011 24th Canadian Conference on', citation['source'])
        self.assertTrue('Islam', citation['creatorLast'])


class PublicationView(TestCase):

    def test_publication_view_redirect(self):
        """ Checks that if item is a journal, it redirects to the 'search.serialssolutions.com' page for now. """
        ourl = '?sid=FirstSearch%3AWorldCat&genre=journal&issn=0017-811X&eissn=2161-976X&title=Harvard+law+review.&date=1887&id=doi%3A&pid=<accession+number>1751808<%2Faccession+number><fssessid>0<%2Ffssessid>&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&req_dat=<sessionid>0<%2Fsessionid>&rfe_dat=<accessionnumber>1751808<%2Faccessionnumber>&rft_id=info%3Aoclcnum%2F1751808&rft_id=urn%3AISSN%3A0017-811X&rft.jtitle=Harvard+law+review.&rft.issn=0017-811X&rft.eissn=2161-976X&rft.aucorp=Harvard+Law+Review+Publishing+Association.%3BHarvard+Law+Review+Association.&rft.place=Cambridge++Mass.&rft.pub=Harvard+Law+Review+Pub.+Association&rft.genre=journal&checksum=059306b04e1938ee38f852a498bea79e&title=Brown%20University&linktype=openurl&detail=RBN'
        client = Client()
        response = client.get('/find/%s/' % ourl)
        self.assertEqual( 302, response.status_code )  # 302/Found, not 301/Permanent
