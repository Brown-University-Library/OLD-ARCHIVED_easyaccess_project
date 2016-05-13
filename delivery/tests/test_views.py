
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from delivery import views
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.utils.module_loading import import_module


log = logging.getLogger('access')
log.debug( 'testing123' )


class SessionHack(object):
    ## based on: http://stackoverflow.com/questions/4453764/how-do-i-modify-the-session-in-the-django-test-framework

    def __init__(self, client):
        ## workaround for issue: http://code.djangoproject.com/ticket/10899
        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key


class AvailabilityViewTest(TestCase):
    """ Checks availability views """

    def setUp(self):
        self.client = Client()
        self.session_hack = SessionHack( self.client )

    def test_availability_direct(self):
        """ Direct hit should redirect to 'find'. """
        response = self.client.get( '/borrow/availability/?foo=bar' )  # project root part of url is assumed
        # print( 'response.content, ```{}```'.format(response.content) )
        # print( 'response.__dict__, ```{}```'.format(response.__dict__) )
        self.assertEqual( 302, response.status_code )
        self.assertEqual( '/find/?foo=bar', response._headers['location'][1] )

    def test_availability_from_findit(self):
        """ Good hit should return response. """
        session = self.session_hack.session
        session['last_path'] = '/easyaccess/find/'
        session['last_querystring'] = 'isbn=123'
        session.save()
        response = self.client.get( '/borrow/availability/?isbn=123' )
        self.assertEqual( 200, response.status_code )
        self.assertTrue( 'easyBorrow' in response.content )

    def test_availability_w_ebook(self):
        """ Good hit should return response. """
        session = self.session_hack.session
        session['last_path'] = '/easyaccess/find/'
        session['last_querystring'] = 'isbn=123'
        session['ebook_json'] = json.dumps( {'ebook_label': 'label_foo', 'ebook_url': 'http://test_url'} )
        session.save()
        response = self.client.get( '/borrow/availability/?isbn=123' )
        self.assertEqual( 200, response.status_code )
        self.assertTrue( '<a href="http://test_url" class="ebook_url">label_foo</a>' in response.content.decode('utf-8') )


    # end AvailabilityViewTest()


class LoginViewTest(TestCase):
    """ Checks availability views """

    def setUp(self):
        self.client = Client()
        self.session_hack = SessionHack( self.client )

    def test_hit_availability_with_no_session(self):
        """ Direct hit with no session info should redirect to 'find'. """
        response = self.client.get( '/borrow/availability/?foo=bar', SERVER_NAME="127.0.0.1" )
        # print( 'response.content, ```{}```'.format(response.content) )
        # print( 'response.__dict__, ```{}```'.format(response.__dict__) )
        self.assertEqual( 302, response.status_code )
        self.assertEqual( '/find/?foo=bar', response._headers['location'][1] )

    def test_hit_shib_login_from_availability_clean(self):
        """ Hitting shib_login with good session info should redirect to login_handler. """
        session = self.session_hack.session
        session['last_path'] = '/easyaccess/borrow/availability/'
        session['last_querystring'] = 'isbn=123'
        session['shib_status'] = ''
        session.save()
        response = self.client.post( '/borrow/shib_login/', SERVER_NAME="127.0.0.1" )
        log.debug( 'response.status_code, {}'.format(response.status_code) )
        self.assertEqual( 302, response.status_code )
        # log.debug( 'response.headers, {}'.format(response._headers) )
        # self.assertTrue( 'shib_logout.jsp' in response._headers['location'][1] )
        # self.assertTrue( '/borrow/login/' in response._headers['location'][1] )
        self.assertEqual( '/borrow/login_handler/', response._headers['location'][1] )

    def test_hit_login_handler_with_availability_last_path(self):
        """ Hitting login_handler with good session info should redirect to process_request. """
        session = self.session_hack.session
        session['last_path'] = '/easyaccess/borrow/availability/'
        session['last_querystring'] = 'isbn=123'
        session['shib_status'] = 'will_force_logout'
        session.save()
        response = self.client.get( '/borrow/login_handler/', SERVER_NAME="127.0.0.1" )
        print( 'location, ```{}```'.format(response._headers['location'][1]) )
        self.assertEqual( 302, response.status_code )
        self.assertEqual( '/borrow/process_request/?isbn=123', response._headers['location'][1] )

    # end LoginViewTest()


class ProcessViewTest(TestCase):
    """ Checks views.process_request()
        Note: am not testing a 'good' hit of process_request() to avoid any chance of executing an ezb request. """

    def setUp(self):
        self.client = Client()
        # self.session_hack = SessionHack( self.client )

    def test_hit_process_directly_nofollow(self):
        """ Direct hit should redirect to /find/?a=b. """
        response = self.client.get( '/borrow/process_request/?isbn=123' )
        self.assertEqual( 302, response.status_code )
        self.assertEqual( '/find/?isbn=123', response._headers['location'][1] )

    # def test_hit_process_directly_follow_redirect(self):
    #     """ Direct hit should redirect to /find/?a=b. """
    #     response = self.client.get( '/borrow/process_request/?isbn=123', follow=True )
    #     # log.debug( 'response.context, ```{}```'.format(pprint.pformat(response.context)) )
    #     self.assertEqual( True, "This article couldn't be located" in response.content )

    def test_hit_process_directly_follow_redirect(self):
        """ Direct hit should redirect to /find/?a=b. """
        response = self.client.get( '/borrow/process_request/?isbn=123', follow=True )
        # log.debug( 'response.context, ```{}```'.format(pprint.pformat(response.context)) )
        self.assertEqual( True, 'div id="citation-linker"' in response.content )  # first redirects back to '/find/?isbn=123', then to 'find/citation_form/?isbn=123'

    # def test_hit_process_properly(self):
    #     """ Direct hit should redirect to 'message' with a link to findit/find. """
    #     session = self.session_hack.session
    #     session['last_path'] = '/easyaccess/borrow/login/'
    #     session['last_querystring'] = 'isbn=123'
    #     session.save()
    #     response = self.client.get( '/borrow/process_request/?isbn=123', follow=True )
    #     self.assertEqual( '/borrow/process_request/', response.context['last_path'] )
    #     self.assertEqual( True, 'Your request was successful' in response.context['message'] )

    # end class ProcessViewTest()






# class ConferenceReportResolverTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#     def test_econference_report(self):
#         request = self.factory.get('?id=10.1109/CCECE.2011.6030651')
#         response = views.ResolveView(request=request)
#         context = response.get_context_data()
#         citation = context['citation']
#         self.assertTrue('Electrical and Computer Engineering (CCECE), 2011 24th Canadian Conference on', citation['source'])
#         self.assertTrue('Islam', citation['creatorLast'])



# class ResolverTest(unittest.TestCase):
# class ResolverTest( TestCase ):
#     def setUp(self):
#         self.factory = RequestFactory()
#         #Settings for test client - http://stackoverflow.com/questions/4453764/how-do-i-modify-the-session-in-the-django-test-framework
#         settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
#         engine = import_module(settings.SESSION_ENGINE)
#         store = engine.SessionStore()
#         store.save()
#         self.session = store

#     def test_unicode(self):
#         """
#         No assertions.  Just make sure we are able to load the context.
#         """
#         q = u'?sid=FirstSearch:WorldCat&genre=book&isbn=9783835302334&title=Das "Orakel der Deisten" : Shaftesbury und die deutsche Aufklärung&date=2008&aulast=Dehrmann&aufirst=Mark-Georg&id=doi:&pid=<accession number>228805805</accession number><fssessid>0</fssessid>&url_ver=Z39.88-2004&rfr_id=info:sid/firstsearch.oclc.org:WorldCat&rft_val_fmt=info:ofi/fmt:kev:mtx:book&req_dat=<sessionid>0</sessionid>&rfe_dat=<accessionnumber>228805805</accessionnumber>&rft_id=info:oclcnum/228805805&rft_id=urn:ISBN:9783835302334&rft.aulast=Dehrmann&rft.aufirst=Mark-Georg&rft.btitle=Das "Orakel der Deisten" : Shaftesbury und die deutsche Aufklärung&rft.date=2008&rft.isbn=9783835302334&rft.place=Göttingen&rft.pub=Wallstein&rft.genre=book&rfe_dat=<dissnote>Thesis (doctoral)--Freie Universität, Berlin, 2006.</dissnote>'
#         request = self.factory.get(q)
#         request.session = self.session
#         response = views.ResolveView(request=request)
#         get = response.get(request)
#         context = response.get_context_data()

#         q = u'?rft.title=“iñtërnâtiônàlĭzætiøn”'
#         request = self.factory.get(q)
#         request.session = self.session
#         response = views.ResolveView(request=request)
#         get = response.get(request)
#         context = response.get_context_data()

#         self.assertEqual( 'a', 'b' )
