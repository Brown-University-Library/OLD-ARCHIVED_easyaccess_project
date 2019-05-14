# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
# from bs4 import BeautifulSoup  # https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from django.conf import settings
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django.utils.module_loading import import_module
from findit import app_settings, utils, views


settings.BUL_LINK_CACHE_TIMEOUT = 0
log = logging.getLogger(__name__)
log.debug( 'logging ready' )


# import logging
# existing_logger_names = logging.getLogger().manager.loggerDict.keys()
# print( '- EXISTING_LOGGER_NAMES, `%s`' % existing_logger_names )


# class SessionHack(object):
#     ## based on: http://stackoverflow.com/questions/4453764/how-do-i-modify-the-session-in-the-django-test-framework

#     def __init__(self, client):
#         ## workaround for issue: http://code.djangoproject.com/ticket/10899
#         settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
#         engine = import_module(settings.SESSION_ENGINE)
#         store = engine.SessionStore()
#         store.save()
#         self.session = store
#         client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key


class RootTest( TestCase ):
    """ Checks slash redirect. """

    def test_root_url_no_slash(self):
        """ Checks '/easyaccess'. """
        response = self.client.get( '' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        redirect_url = response._headers['location'][1]
        self.assertEqual(  '/find/', redirect_url )

    def test_root_url_no_slash(self):
        """ Checks '/easyaccess/'. """
        response = self.client.get( '' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        redirect_url = response._headers['location'][1]
        self.assertEqual(  '/find/', redirect_url )

    # end class RootTest()


class IndexPageLinksTest( TestCase ):
    """ Checks example links on index page. """

    def setUp(self):
        self.client = Client()

    # def test_index(self):
    #     """ Checks main index page. """
    #     response = self.client.get( '/find/' )  # project root part of url is assumed
    #     self.assertEqual( 200, response.status_code )
    #     self.assertEqual( True, '<title>easyAccess</title>' in response.content.decode('utf-8') )
    #     self.assertEqual( True, '<h3>easyAccess</h3>' in response.content.decode('utf-8') )
    #     self.assertEqual( True, 'class="intro">Article Examples' in response.content.decode('utf-8') )

    def test_index(self):
        """ Checks main index page. """
        response = self.client.get( '/find/' )  # project root part of url is assumed
        html = response.content.decode('utf-8')
        self.assertEqual( 200, response.status_code )
        self.assertInHTML( '<title>easyAccess</title>', html )
        self.assertInHTML( '<h1>easyAccess &mdash; info</h1>', html )
        self.assertInHTML( '<h3 class="intro">Article Examples</h3>', html )

    def test_article_held_electronically(self):
        """ Checks the `Article held electronically.` link.
            Should redirect right to article, or display landing page depending on FLY_TO_FULLTEXT setting. """
        response = self.client.get( '/find/?sid=google&auinit=T&aulast=SOTA&atitle=Phylogeny+and+divergence+time+of+island+tiger+beetles+of+the+genus+Cylindera+(Coleoptera:+Cicindelidae)+in+East+Asia&id=doi:10.1111/j.1095-8312.2011.01617.x&title=Biological+journal+of+the+Linnean+Society&volume=102&issue=4&date=2011&spage=715&issn=0024-4066' )
        if app_settings.FLY_TO_FULLTEXT is True:
            self.assertEqual( 302, response.status_code )
            redirect_url = response._headers['location'][1]
            self.assertEqual(
                'https://login.revproxy.brown.edu/login?url=http://doi.wiley.com/10.1111/j.1095-8312.2011.01617.x',
                redirect_url )
        else:
            content = response.content.decode( 'utf-8' )
            # log.debug( 'content, ```%s```' % content )
            self.assertEqual( 200, response.status_code )
            self.assertTrue( 'easyAccess &rarr; easyArticle' in content )

    def test_article_chapter_held_at_annex(self):
        """ Checks the `Article/Chapter held at Annex.` link """
        from findit.models import PrintTitle
        print_title = PrintTitle(
            key='003776861966', issn='0037-7686', start='1966', end='1992', location='Annex', call_number='BL60.A2 S65' )
        print_title.save()
        response = self.client.get( '/find/?genre=article&issn=00377686&title=Social+Compass&volume=14&issue=5/6&date=19670901&atitle=Religious+knowledge+and+attitudes+in+Mexico+City.&spage=469&pages=469-482&sid=EBSCO:Academic+Search+Premier&aulast=Stryckman,+Paul' )
        content = response.content.decode( 'utf-8' )
        # log.debug( 'content, ```%s```' % content.decode('utf-8') )
        self.assertEqual( 200, response.status_code )
        self.assertInHTML( '<title>easyAccess &rarr; easyArticle</title>', content )
        self.assertInHTML( '<h4 class="easy_what">easyArticle</h4>', content )
        # self.assertEqual( True, '<h2>Available at the library</h2>' in content )
        self.assertInHTML( '<h2>Available at the library</h2>', content )
        self.assertEqual( True, 'request for delivery via josiah' in content.lower() )
        self.assertEqual( True, 'BL60.A2 S65 -- ANNEX' in content )

    ## end class IndexPageLinksTest


class GenreEqualsBookItemTest(TestCase):
    """ Checks handling of genre=bookitem that should be genre=article. """

    def test_bad_bookitem(self):
        response = self.client.get( '/find/',
            {'atitle': 'The Effects of Normalization, Transformation, and Rarefaction on Clustering of OTU Abundance',
             'au': 'Tomlinson, DeAndre A.',
             'date': '20181201',
             'ebscoperma_link': 'http://search.ebscohost.com/login.aspx?direct=true&site=eds-live&scope=site&db=edseee&AN=edseee.8621347&authtype=ip,sso&custid=rock',
             'genre': 'bookitem',
             'isbn': '9781538654880',
             'pages': '2810-2812',
             'sid': 'EBSCO:IEEE Xplore Digital Library',
             'spage': '2810',
             'title': '2018 IEEE International Conference on Bioinformatics and Biomedicine (BIBM), Bioinformatics and Biomedicine (BIBM), 2018 IEEE International Conference on'
             }
         )
        self.assertEqual( 302, response.status_code )
        redirect_url = response._headers['location'][1]
        self.assertTrue( 'genre=article' in redirect_url )

    ## end class GenreEqualsBookItemTest()


class PmidResolverTest(TestCase):
    """ New version of above. Under construction """

    def test_pmid(self):
        """ Pubmed request - locally-held at Annex, and no direct link.
            Should show W.H.O. link, and local Annex holding. """
        from findit.models import PrintTitle
        print_title = PrintTitle(
            key='051230541950', issn='0512-3054', start='1950', end='2015', location='Annex', call_number='RA8 .A27' )
        print_title.save()
        url = '/find/?pmid=11234459'
        c = Client()
        response = c.get( url )
        html = response.content
        # log.debug( 'html, ```%s```' % html )
        self.assertEqual( True, 'available online' in html.lower() )
        self.assertEqual( True, 'https://login.revproxy.brown.edu/login?url=http://search.who.int/search?' in html )
        self.assertEqual( True, 'request for delivery via josiah' in html.lower() )
        self.assertEqual( True, 'RA8 .A27 -- ANNEX' in html )

    # end class PmidResolverTest


class PrintResolverTest(TestCase):

    def test_print_holding(self):
        """ Checks held-book context. """
        url = '/find/?genre=article&issn=01639374&title=Cataloging%20&%20Classification%20Quarterly&volume=10&issue=3&date=19900101&atitle=Would%20the%20reintroduction%20of%20latest%20entry%20cataloging%20create%20more%20problems%20than%20it%20would%20resolve%3F&spage=35&pages=35-44&sid=EBSCO:Library%2C%20Information%20Science%20%26%20Technology%20Abstracts&au=Mering,%20M%20V'
        c = Client()
        response = c.get( url, SERVER_NAME='127.0.0.1' )
        # log.debug( 'context.keys(), `%s`' % pprint.pformat( sorted(response.context.keys()) ) )
        citation = response.context['citation']
        link_groups = response.context['link_groups']
        # log.debug( 'citation, `%s`' % pprint.pformat(citation) )
        # log.debug( 'link_groups, `%s`' % pprint.pformat(link_groups) )
        self.assertEqual( 'Cataloging & classification quarterly', citation['source'] )
        self.assertEqual( 'Mering', citation['creatorLast'] )
        self.assertEqual( 'Library Specific Holdings', link_groups[0]['holdingData']['providerName'] )

    # end class PrintResolverTest


class EasyBorrowResolverTest(TestCase):

    def test_pass_to_easy_borrow(self):
        """ Checks that book request hands off to easyBorrow landing page. """
        url = '/find/?sid=FirstSearch%3AWorldCat&genre=book&isbn=9780394565279&title=The+risk+pool&date=1988&aulast=Russo&aufirst=Richard&id=doi%3A&pid=%3Caccession+number%3E17803510%3C%2Faccession+number%3E%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3E1st+ed.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E17803510%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F17803510&rft_id=urn%3AISBN%3A9780394565279&rft.aulast=Russo&rft.aufirst=Richard&rft.btitle=The+risk+pool&rft.date=1988&rft.isbn=9780394565279&rft.place=New+York&rft.pub=Random+House&rft.edition=1st+ed.&rft.genre=book&checksum=d6c1576188e0f87ac13f4c4582382b4f&title=Brown University&linktype=openurl&detail=RBN'
        c = Client()
        response = c.get( url, SERVER_NAME='127.0.0.1' )
        self.assertEqual( 302, response.status_code )
        redirect_url = response._headers['location'][1]
        self.assertEqual( '/borrow/availability/?sid=FirstSearch%3AWorldCat&genre=book', redirect_url[0:59] )

    ## end class EasyBorrowResolverTest


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
        self.assertEqual( '/borrow/availability/?rft.pub=Yale+University+Press&rft.aulast=Dyson', redirect_url[0:68] )

    # end class EbookResolverTest


class ConferenceReportResolverTest(TestCase):

    def test_econference_report(self):
        """ Checks conference-report resolution for minimal id where sersol lookup indicates book.
            Should redirect to `borrow` url where easyBorrow request button will appear and any online options will appear. """
        url = '/find/?id=10.1109/CCECE.2011.6030651'
        c = Client()
        response = c.get( url, SERVER_NAME='127.0.0.1' )
        redirect_url = response._headers['location'][1]
        # log.debug( 'redirect_url, ```%s```' % redirect_url )
        self.assertEqual( '/borrow/availability/?id=10.1109/CCECE.2011.6030651', redirect_url )

    # end class ConferenceReportResolverTest


class PublicationView(TestCase):

    def test_publication_view_redirect(self):
        """ Checks that if item is a journal, it redirects to the 'search.serialssolutions.com' page for now. """
        ourl = '?sid=FirstSearch%3AWorldCat&genre=journal&issn=0017-811X&eissn=2161-976X&title=Harvard+law+review.&date=1887&id=doi%3A&pid=<accession+number>1751808<%2Faccession+number><fssessid>0<%2Ffssessid>&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&req_dat=<sessionid>0<%2Fsessionid>&rfe_dat=<accessionnumber>1751808<%2Faccessionnumber>&rft_id=info%3Aoclcnum%2F1751808&rft_id=urn%3AISSN%3A0017-811X&rft.jtitle=Harvard+law+review.&rft.issn=0017-811X&rft.eissn=2161-976X&rft.aucorp=Harvard+Law+Review+Publishing+Association.%3BHarvard+Law+Review+Association.&rft.place=Cambridge++Mass.&rft.pub=Harvard+Law+Review+Pub.+Association&rft.genre=journal&checksum=059306b04e1938ee38f852a498bea79e&title=Brown%20University&linktype=openurl&detail=RBN'
        client = Client()
        response = client.get('/find/%s/' % ourl)
        self.assertEqual( 302, response.status_code )  # 302/Found, not 301/Permanent
