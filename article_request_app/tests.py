# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, os, pprint, random
from types import NoneType

from . import settings_app
from .classes.illiad_helper import NewIlliadHelper  # under development
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
        response = self.client.get( '/article_request/login_handler/?a=b', SERVER_NAME="127.0.0.1" )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )
        redirect_url = response._headers['location'][1]
        self.assertEqual( '/find/?a=b', redirect_url )

    def test_direct_login_good_session(self):
        """ If a good request, should redirect to display submission page. """
        # session = self.session_hack.session
        # session['last_path'] = '/easyaccess/find/'
        # session['last_querystring'] = 'foo'
        # session.save()
        response = self.client.get( '/article_request/login_handler/?citation_json=aa&format=bb&illiad_url=cc&querystring=the_querystring', SERVER_NAME="127.0.0.1" )  # project root part of url is assumed
        redirect_url = response._headers['location'][1]
        self.assertEqual( 'http://127.0.0.1/article_request/illiad/?the_querystring', redirect_url )

    def test_direct_article_request_no_session(self):
        """ If not from '/easyaccess/article_request/login_handler/', should redirect to index page. """
        ## without session
        response = self.client.get( '/article_request/illiad/?a=b', SERVER_NAME="127.0.0.1" )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )
        redirect_url = response._headers['location'][1]
        self.assertEqual( '/find/?a=b', redirect_url )

    def test_direct_article_request_good_session(self):
        """ If from '/easyaccess/article_request/login_handler/', should display page. """
        ## with session
        session = self.session_hack.session
        session['last_path'] = '/easyaccess/article_request/login_handler/'
        # session['last_querystring'] = 'isbn=123'
        session.save()
        response = self.client.get( '/article_request/illiad/?a=b', SERVER_NAME="127.0.0.1" )  # project root part of url is assumed
        self.assertEqual( 200, response.status_code )
        self.assertTrue( 'Please click submit to confirm.' in response.content )

    # end class ViewsTest()


class NewIlliadHelperTest( TestCase ):
    """ Tests classes.illiad_helper.NewIlliadHelper() """

    def setUp(self):
        self.helper = NewIlliadHelper()

    def test_connect__good(self):
        """ Known good user connection should return logged-in status, no error-message, and registered status. """
        ill_username = settings_app.TEST_ILLIAD_GOOD_USERNAME
        result_dct = self.helper._connect( ill_username )
        self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
        self.assertEqual( None, result_dct['error_message'] )
        self.assertEqual( dict, type(result_dct['illiad_login_dct']) )
        self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
        self.assertEqual( False, result_dct['is_blocked'] )
        self.assertEqual( True, result_dct['is_logged_in'] )
        self.assertEqual( False, result_dct['is_new_user'] )
        self.assertEqual( True, result_dct['is_registered'] )
        result_dct['illiad_session_instance'].logout()

    def test_connect__newuser(self):
        """ New-user connection should return unregistered status. """
        ill_username = '{test_root}{random}'.format( test_root=settings_app.TEST_ILLIAD_NEW_USER_ROOT, random=random.randint(11111, 99999) )
        result_dct = self.helper._connect( ill_username )
        self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
        self.assertEqual( None, result_dct['error_message'] )
        self.assertEqual( dict, type(result_dct['illiad_login_dct']) )
        self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
        self.assertEqual( False, result_dct['is_blocked'] )
        self.assertEqual( True, result_dct['is_logged_in'] )
        self.assertEqual( False, result_dct['is_new_user'] )  # odd; perhaps all remote-auth connections indicate this
        self.assertEqual( False, result_dct['is_registered'] )  # key indicator used in subsequent code

    def test_connect__blocked(self):
        """ Blocked user connection should return is_blocked as True. """
        ill_username = settings_app.TEST_ILLIAD_BLOCKED_USERNAME
        result_dct = self.helper._connect( ill_username )
        self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
        self.assertEqual( None, result_dct['error_message'] )  # populated by login_user()
        self.assertEqual( dict, type(result_dct['illiad_login_dct']) )
        self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
        self.assertEqual( True, result_dct['is_blocked'] )
        self.assertEqual( False, result_dct['is_logged_in'] )
        self.assertEqual( False, result_dct['is_new_user'] )
        self.assertEqual( False, result_dct['is_registered'] )
        result_dct['illiad_session_instance'].logout()

    def test_connect__disavowed(self):
        """ Disavowed user connection should contain correct error_message. """
        ill_username = settings_app.TEST_ILLIAD_DISAVOWED_USERNAME
        result_dct = self.helper._connect( ill_username )
        self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
        self.assertTrue( 'there may be an issue with your ILLiad account' in result_dct['error_message'] )
        self.assertEqual( NoneType, type(result_dct['illiad_login_dct']) )
        self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
        self.assertEqual( None, result_dct['is_blocked'] )
        self.assertEqual( None, result_dct['is_logged_in'] )
        self.assertEqual( None, result_dct['is_new_user'] )
        self.assertEqual( None, result_dct['is_registered'] )
        result_dct['illiad_session_instance'].logout()

    def test_login_user__good(self):
        """ Known good user should return success as True. """
        user_dct = { 'eppn': '{}@brown.edu'.format(settings_app.TEST_ILLIAD_GOOD_USERNAME) }
        item_dct = {}  # needed for error-message preparation
        result_dct = self.helper.login_user( user_dct, item_dct )
        self.assertEqual( ['error_message', 'illiad_session_instance', 'success'], sorted(result_dct.keys()) )
        self.assertEqual( None, result_dct['error_message'] )
        self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
        self.assertEqual( True, result_dct['success'] )
        result_dct['illiad_session_instance'].logout()

    def test_login_user__blocked(self):
        1/0
        """ Known blocked user should ... """
        user_dct = { 'eppn': '{}@brown.edu'.format(settings_app.TEST_ILLIAD_GOOD_USERNAME) }
        item_dct = {}  # needed for error-message preparation
        result_dct = self.helper.login_user( user_dct, item_dct )
        self.assertEqual( ['error_message', 'illiad_session_instance', 'success'], sorted(result_dct.keys()) )
        self.assertEqual( 2, result_dct['error_message'] )
        self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
        self.assertEqual( 2, result_dct['illiad_session_instance'].registered )
        self.assertEqual( 2, result_dct['success'] )
        result_dct['illiad_session_instance'].logout()

    def test_login__newuser(self):
        """ New-user connection should ? """
        username = '{test_root}{random}'.format( test_root=settings_app.TEST_ILLIAD_NEW_USER_ROOT, random=random.randint(11111, 99999) )
        user_dct = {
            'eppn': '{}@brown.edu'.format(username),
            'name_first': 'test_firstname',
            'name_last': 'test_lastname',
            'email': 'test@test.edu',
            'brown_type': 'test_brown_type',
            'phone': 'test_phone',
            'department': 'test_department'
            }
        item_dct = {}  # needed for error-message preparation
        result_dct = self.helper.login_user( user_dct, item_dct )
        self.assertEqual( ['error_message', 'illiad_session_instance', 'success'], sorted(result_dct.keys()) )
        self.assertEqual( None, result_dct['error_message'] )
        self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
        self.assertEqual( True, result_dct['illiad_session_instance'].registered )
        self.assertEqual( True, result_dct['success'] )

    # def test_login__disavowed(self):
        # TODO

    # end class IlliadHelperTest()


class LoginHelper_Test( TestCase ):
    """ Tests classes.LoginHelper() """

    def setUp( self ):
        self.helper = LoginHelper()

    ## TODO: re-enable after rework

    # def test__check_referrer( self ):
    #     """ Tests whether referrer is valid. """
    #     ## empty request should fail
    #     client = Client()
    #     session = client.session
    #     meta_dict = {}
    #     self.assertEqual(
    #         ( False, '/find/?' ),  # ( referrer_ok, redirect_url )
    #         self.helper.check_referrer(session, meta_dict) )
    #     ## good request should return True
    #     client = Client()
    #     session = client.session
    #     # session['findit_illiad_check_flag'] = 'good'
    #     # session['findit_illiad_check_enhanced_querystring'] = 'querystring_a'
    #     # meta_dict = { 'QUERY_STRING': 'querystring_a' }
    #     session['last_path'] = '/easyaccess/find/'
    #     session['last_querystring'] = 'isbn=123'
    #     self.assertEqual(
    #         ( True, '' ),  # ( referrer_ok, redirect_url )
    #         self.helper.check_referrer(session, meta_dict) )

    # end class LoginHelper_Test
