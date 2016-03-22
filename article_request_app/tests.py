# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, os, pprint
from .classes.login_helper import LoginHelper
from django.conf import settings
from django.http import HttpRequest
from django.test import Client, TestCase
from django.utils.module_loading import import_module


log = logging.getLogger( 'access' )
TestCase.maxDiff = None


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


class ViewsTest( TestCase ):
    """ Tests views via Client. """

    def setUp(self):
        self.client = Client()
        self.session_hack = SessionHack( self.client )

    def test_direct_login_no_session(self):
        """ If not from '/easyaccess/find/', should redirect to index page. """
        response = self.client.get( '/article_request/login/?a=b' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )
        redirect_url = response._headers['location'][1]
        self.assertEqual( '/find/?a=b', redirect_url )

    def test_direct_login_good_session(self):
        """ If from '/easyaccess/find/', should redirect self. """
        session = self.session_hack.session
        session['last_path'] = '/easyaccess/find/'
        session['last_querystring'] = 'isbn=123'
        session.save()
        response = self.client.get( '/article_request/login/?a=b' )  # project root part of url is assumed
        redirect_url = response._headers['location'][1]
        self.assertEqual( 'sso.brown.edu', redirect_url[8:21] )

    def test_direct_article_request_no_session(self):
        """ If not from '/easyaccess/article_request/login/', should redirect to index page. """
        ## without session
        response = self.client.get( '/article_request/illiad/?a=b' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )
        redirect_url = response._headers['location'][1]
        self.assertEqual( '/find/?a=b', redirect_url )

    def test_direct_article_request_good_session(self):
        """ If from '/easyaccess/article_request/login/', should display page. """
        ## with session
        session = self.session_hack.session
        session['last_path'] = '/easyaccess/article_request/login/'
        # session['last_querystring'] = 'isbn=123'
        session.save()
        response = self.client.get( '/article_request/illiad/?a=b' )  # project root part of url is assumed
        self.assertEqual( 200, response.status_code )
        self.assertTrue( 'Please click submit to confirm.' in response.content )

    # end class ViewsTest()


class LoginHelper_Test( TestCase ):
    """ Tests classes.LoginHelper() """

    def setUp( self ):
        self.helper = LoginHelper()

    def test__check_referrer( self ):
        """ Tests whether referrer is valid. """
        ## empty request should fail
        client = Client()
        session = client.session
        meta_dict = {}
        self.assertEqual(
            ( False, '/find/?' ),  # ( referrer_ok, redirect_url )
            self.helper.check_referrer(session, meta_dict) )
        ## good request should return True
        client = Client()
        session = client.session
        # session['findit_illiad_check_flag'] = 'good'
        # session['findit_illiad_check_enhanced_querystring'] = 'querystring_a'
        # meta_dict = { 'QUERY_STRING': 'querystring_a' }
        session['last_path'] = '/easyaccess/find/'
        session['last_querystring'] = 'isbn=123'
        self.assertEqual(
            ( True, '' ),  # ( referrer_ok, redirect_url )
            self.helper.check_referrer(session, meta_dict) )

    def test__assess_shib_redirect_need( self ):
        """ Tests whether a shib logout or login url needs to be built. """
        ## localdev never needs shib redirect
        session = {}
        host = '127.0.0.1'
        meta_dict = {}
        ( localdev_check, redirect_check, shib_status ) = self.helper.assess_shib_redirect_need( session, host, meta_dict )
        self.assertEqual( True, localdev_check )
        self.assertEqual( False, redirect_check )
        ## clean entry needs logout-redirect
        session = { 'shib_status': '' }
        host = 'foo'
        meta_dict = {}
        ( localdev_check, redirect_check, shib_status ) = self.helper.assess_shib_redirect_need( session, host, meta_dict )
        self.assertEqual( False, localdev_check )
        self.assertEqual( True, redirect_check )
        ## logout was forced; needs login-redirect
        session = { 'shib_status': 'will_force_logout' }
        host = 'foo'
        meta_dict = {}
        ( localdev_check, redirect_check, shib_status ) = self.helper.assess_shib_redirect_need( session, host, meta_dict )
        self.assertEqual( False, localdev_check )
        self.assertEqual( True, redirect_check )
        self.assertEqual( 'will_force_logout', shib_status )
        ## login was forced and shib headers filled; good, no redirect
        session = { 'shib_status': 'will_force_login' }
        host = 'foo'
        meta_dict = { 'Shibboleth-eppn': 'foo' }
        ( localdev_check, redirect_check, shib_status ) = self.helper.assess_shib_redirect_need( session, host, meta_dict )
        self.assertEqual( False, localdev_check )
        self.assertEqual( False, redirect_check )
        self.assertEqual( 'will_force_login', shib_status )
        ## 'will_force_login' normally good, but this needs shib-headers regrabbed
        session = { 'shib_status': 'will_force_login' }
        host = 'foo'
        meta_dict = { 'Shibboleth-eppn': '' }
        ( localdev_check, redirect_check, shib_status ) = self.helper.assess_shib_redirect_need( session, host, meta_dict )
        self.assertEqual( False, localdev_check )
        self.assertEqual( True, redirect_check )
        self.assertEqual( 'will_force_logout', shib_status )

    def test__build_shib_redirect_url( self ):
        """ Tests the redirect-url. """
        ## clean entry
        ( redirect_url, updated_shib_status ) = self.helper.build_shib_redirect_url(
            shib_status='', scheme='https', host='foo.edu', session_dct={'login_openurl':'a=b&c=d'}, meta_dct={} )
        self.assertTrue( 'logout' in redirect_url )
        self.assertEqual( 'will_force_logout', updated_shib_status )
        ## logout was forced; needs login-redirect
        ( redirect_url, updated_shib_status ) = self.helper.build_shib_redirect_url(
            shib_status='will_force_logout', scheme='https', host='foo.edu', session_dct={'login_openurl':'a=b&c=d'}, meta_dct={} )
        self.assertTrue( 'login' in redirect_url )
        self.assertEqual( 'will_force_login', updated_shib_status )
        ## 'will_force_login' normally good, but this needs shib-headers regrabbed
        ( redirect_url, updated_shib_status ) = self.helper.build_shib_redirect_url(
            shib_status='will_force_login', scheme='https', host='foo.edu', session_dct={'login_openurl':'a=b&c=d'}, meta_dct={'Shibboleth-eppn': ''} )
        self.assertTrue( 'logout' in redirect_url )
        self.assertEqual( 'will_force_logout', updated_shib_status )

    # end class LoginHelper_Test
