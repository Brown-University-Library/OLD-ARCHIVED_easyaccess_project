# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint, random, urlparse
from types import NoneType

from . import settings_app
from .classes.illiad_helper import IlliadApiHelper, NewIlliadHelper  # under development
from .classes.login_helper import LoginHelper
from .classes.shib_helper import ShibLoginHelper
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils.module_loading import import_module


log = logging.getLogger( 'access' )
TestCase.maxDiff = None


class IlliadApiHelperTest( TestCase ):
    """ Tests helper functions for the internal brown illiad-api. """

    def setUp(self):
        self.helper = IlliadApiHelper()

    def test_manage_illiad_user_check__good_existing_user(self):
        """ Checks existing-user response. """
        usr_dct = settings_app.TEST_GOOD_USRDCT
        title = 'foo'
        rspns_dct = self.helper.manage_illiad_user_check( usr_dct, title )
        self.assertEqual( {u'success': True}, rspns_dct )

    # def test_create_new_user(self):
    #     """ Checks response.
    #         KEEP, but... disabled because this will really create a new user. """
    #     usr_dct = settings_app.TEST_GOOD_USRDCT
    #     new_user_auth_id = '%s%s' % ( 'zzzz', random.randint(1111, 9999) )
    #     usr_dct['eppn'] = '%s@brown.edu' % new_user_auth_id
    #     usr_dct['id_short'] = new_user_auth_id
    #     log.debug( 'new usr_dct, ```%s```' % pprint.pformat(usr_dct) )
    #     success_check = self.helper.create_new_user( usr_dct )
    #     self.assertEqual( True, success_check )

    ## end class IlliadApiHelperTest()


class ShibLoginHelperTest( TestCase ):
    """ Tests querystring builder called from views.shib_login() """

    def setUp(self):
        self.helper = ShibLoginHelper()

    def test_build_shib_sp_querystring(self):
        """ Checks localdev querystring. """
        citation_json = '{"param_a": "a\\u00e1a"}'  # json version of {'param_a': 'aáa'}
        format = 'journal'
        illiad_url = 'https://domain/aa/bb/OpenURL?rft.atitle=Stalking the Wild Basenji'
        querystring = 'rft.atitle=Stalking the Wild Basenji'
        log_id = 'foo'
        self.assertEqual(
            'target=%2Feasyaccess%2Farticle_request%2Flogin_handler%2F%3Fcitation_json%3D%257B%2522param_a%2522%253A%2520%2522a%255Cu00e1a%2522%257D%26format%3Djournal%26illiad_url%3Dhttps%253A%2F%2Fdomain%2Faa%2Fbb%2FOpenURL%253Frft.atitle%253DStalking%2520the%2520Wild%2520Basenji%26querystring%3Drft.atitle%253DStalking%2520the%2520Wild%2520Basenji%26ezlogid%3Dfoo',
            self.helper.build_shib_sp_querystring( citation_json, format, illiad_url, querystring, log_id )
        )

    def test_build_localdev_querystring(self):
        """ Checks localdev querystring. """
        citation_json = '{"param_a": "a\\u00e1a"}'  # json version of {'param_a': 'aáa'}
        format = 'journal'
        illiad_url = 'https://domain/aa/bb/OpenURL?rft.atitle=Stalking the Wild Basenji'
        querystring = 'rft.atitle=Stalking the Wild Basenji'
        log_id = 'foo'
        self.assertEqual(
            'citation_json=%7B%22param_a%22%3A%20%22a%5Cu00e1a%22%7D&format=journal&illiad_url=https%3A//domain/aa/bb/OpenURL%3Frft.atitle%3DStalking%20the%20Wild%20Basenji&querystring=rft.atitle%3DStalking%20the%20Wild%20Basenji&ezlogid=foo',
            self.helper.build_localdev_querystring( citation_json, format, illiad_url, querystring, log_id )
        )

    ## end class ShibLoginHelperTest()


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
        response = self.client.get( '/article_request/login_handler/?citation_json=%7b%22foo%22%3a+%22bar%22%7d&format=bb&illiad_url=cc&querystring=the_querystring', SERVER_NAME="127.0.0.1" )  # project root part of url is assumed; &, fyi, ```citation_json={"foo": "bar"}```
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


# class NewIlliadHelperTest( TestCase ):
#     """ Tests classes.illiad_helper.NewIlliadHelper() """

#     def setUp(self):
#         self.helper = NewIlliadHelper()

#     def test_connect__good(self):
#         """ Known good user connection should return logged-in status, no error-message, and registered status. """
#         ill_username = settings_app.TEST_ILLIAD_GOOD_USERNAME
#         result_dct = self.helper._connect( ill_username )
#         self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
#         self.assertEqual( None, result_dct['error_message'] )
#         self.assertEqual( dict, type(result_dct['illiad_login_dct']) )
#         self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#         self.assertEqual( False, result_dct['is_blocked'] )
#         self.assertEqual( True, result_dct['is_logged_in'] )
#         self.assertEqual( False, result_dct['is_new_user'] )
#         self.assertEqual( True, result_dct['is_registered'] )
#         result_dct['illiad_session_instance'].logout()

#     # def test_connect__newuser(self):
#     #     """ New-user connection should return unregistered status.
#     #         Test is good, but is disabled so as not to unnecessarily create new-users in ILLiad. """
#     #     ill_username = '{test_root}{random}'.format( test_root=settings_app.TEST_ILLIAD_NEW_USER_ROOT, random=random.randint(11111, 99999) )
#     #     result_dct = self.helper._connect( ill_username )
#     #     self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
#     #     self.assertEqual( None, result_dct['error_message'] )
#     #     self.assertEqual( dict, type(result_dct['illiad_login_dct']) )
#     #     self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#     #     self.assertEqual( False, result_dct['is_blocked'] )
#     #     self.assertEqual( True, result_dct['is_logged_in'] )
#     #     self.assertEqual( False, result_dct['is_new_user'] )  # odd; perhaps all remote-auth connections indicate this
#     #     self.assertEqual( False, result_dct['is_registered'] )  # key indicator used in subsequent code

#     ## test disabled for now because block indication comes later, on getting the initial request form, not on login.
#     ## the module will have to be reworked.
#     # def test_connect__blocked(self):
#     #     """ Blocked user connection should return is_blocked as True. """
#     #     ill_username = settings_app.TEST_ILLIAD_BLOCKED_USERNAME
#     #     result_dct = self.helper._connect( ill_username )
#     #     self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
#     #     self.assertEqual( None, result_dct['error_message'] )  # populated by login_user()
#     #     self.assertEqual( dict, type(result_dct['illiad_login_dct']) )
#     #     self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#     #     self.assertEqual( True, result_dct['is_blocked'] )
#     #     self.assertEqual( False, result_dct['is_logged_in'] )
#     #     self.assertEqual( False, result_dct['is_new_user'] )
#     #     self.assertEqual( False, result_dct['is_registered'] )
#     #     result_dct['illiad_session_instance'].logout()

#     def test_connect__disavowed(self):
#         """ Disavowed user connection should contain correct error_message. """
#         ill_username = settings_app.TEST_ILLIAD_DISAVOWED_USERNAME
#         result_dct = self.helper._connect( ill_username )
#         self.assertEqual( [ 'error_message', 'illiad_login_dct', 'illiad_session_instance', 'is_blocked', 'is_logged_in', 'is_new_user', 'is_registered', 'submitted_username' ], sorted(result_dct.keys()) )
#         self.assertTrue( 'there may be an issue with your ILLiad account' in result_dct['error_message'] )
#         self.assertEqual( NoneType, type(result_dct['illiad_login_dct']) )
#         self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#         self.assertEqual( None, result_dct['is_blocked'] )
#         self.assertEqual( None, result_dct['is_logged_in'] )
#         self.assertEqual( None, result_dct['is_new_user'] )
#         self.assertEqual( None, result_dct['is_registered'] )
#         result_dct['illiad_session_instance'].logout()

#     def test_login_user__good(self):
#         """ Known good user should return success as True. """
#         user_dct = { 'eppn': '%s@brown.edu' % settings_app.TEST_ILLIAD_GOOD_USERNAME, 'brown_type': 'Staff' }
#         title = 'a_title'  # needed for error-message preparation
#         result_dct = self.helper.login_user( user_dct, title )
#         self.assertEqual( ['error_message', 'illiad_session_instance', 'success'], sorted(result_dct.keys()) )
#         self.assertEqual( None, result_dct['error_message'] )
#         self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#         self.assertEqual( True, result_dct['success'] )
#         result_dct['illiad_session_instance'].logout()

#     # def test_login_user__newuser(self):
#     #     """ New-user connection should return success and show status of registered.
#     #         Test is good, but is disabled so as not to unnecessarily create new-users in ILLiad. """
#     #     username = '{test_root}{random}'.format( test_root=settings_app.TEST_ILLIAD_NEW_USER_ROOT, random=random.randint(11111, 99999) )
#     #     user_dct = {
#     #         'eppn': '{}@brown.edu'.format(username),
#     #         'name_first': 'test_firstname',
#     #         'name_last': 'test_lastname',
#     #         'email': 'test@test.edu',
#     #         'brown_type': 'test_brown_type',
#     #         'phone': 'test_phone',
#     #         'department': 'test_department'
#     #         }
#     #     title = 'a_title'  # needed for error-message preparation
#     #     result_dct = self.helper.login_user( user_dct, title )
#     #     self.assertEqual( ['error_message', 'illiad_session_instance', 'success'], sorted(result_dct.keys()) )
#     #     self.assertEqual( None, result_dct['error_message'] )
#     #     self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#     #     self.assertEqual( True, result_dct['illiad_session_instance'].registered )
#     #     self.assertEqual( True, result_dct['success'] )

#     ## test disabled for now because block indication comes later, on getting the initial request form, not on login.
#     ## the module will have to be reworked.
#     # def test_login_user__blocked(self):
#     #     """ Known blocked user should ... """
#     #     ill_username = settings_app.TEST_ILLIAD_BLOCKED_USERNAME
#     #     user_dct = {
#     #         'eppn': '{}@brown.edu'.format(ill_username),
#     #         'name_first': 'test_firstname',
#     #         'name_last': 'test_lastname',
#     #         'email': 'test@test.edu',
#     #         'brown_type': 'test_brown_type',
#     #         'phone': 'test_phone',
#     #         'department': 'test_department'
#     #     }
#     #     title = 'a_title'  # needed for error-message preparation
#     #     result_dct = self.helper.login_user( user_dct, title )
#     #     self.assertEqual( ['error_message', 'illiad_session_instance', 'success'], sorted(result_dct.keys()) )
#     #     self.assertTrue( 'It appears there is a problem' in result_dct['error_message'] )
#     #     self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#     #     self.assertEqual( True, result_dct['illiad_session_instance'].registered )
#     #     self.assertEqual( False, result_dct['success'] )
#     #     result_dct['illiad_session_instance'].logout()

#     def test_login__disavowed(self):
#         """ Disavowed user login response should contain correct error_message. """
#         ill_username = settings_app.TEST_ILLIAD_DISAVOWED_USERNAME
#         user_dct = {
#             'eppn': '{}@brown.edu'.format(ill_username),
#             'name_first': 'test_firstname',
#             'name_last': 'test_lastname',
#             'email': 'test@test.edu',
#             'brown_type': 'test_brown_type',
#             'phone': 'test_phone',
#             'department': 'test_department'
#         }
#         title = 'a_title'  # needed for error-message preparation
#         result_dct = self.helper.login_user( user_dct, title )
#         self.assertEqual( ['error_message', 'illiad_session_instance', 'success'], sorted(result_dct.keys()) )
#         self.assertTrue( 'there may be an issue with your ILLiad account' in result_dct['error_message'] )
#         self.assertEqual( "<type 'instance'>", unicode(type(result_dct['illiad_session_instance'])) )
#         self.assertEqual( False, result_dct['illiad_session_instance'].registered )
#         self.assertEqual( False, result_dct['success'] )
#         result_dct['illiad_session_instance'].logout()

#     # end class NewIlliadHelperTest()


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
    #     session['last_path'] = reverse( 'findit:findit_base_resolver_url' )
    #     session['last_querystring'] = 'isbn=123'
    #     self.assertEqual(
    #         ( True, '' ),  # ( referrer_ok, redirect_url )
    #         self.helper.check_referrer(session, meta_dict) )

    def test_check_if_authorized__bad_data(self):
        """ Bad data should return False. """
        shib_dct = {}
        ( is_authorized, redirect_url, message ) = self.helper.check_if_authorized(shib_dct)
        self.assertEqual( False, is_authorized )
        self.assertEqual( '/article_request/shib_logout/', redirect_url )
        self.assertTrue( 'you are not authorized' in message )

    def test_check_if_authorized__good_data(self):
        """ Good data should return True. """
        shib_dct = { 'member_of': settings_app.REQUIRED_GROUPER_GROUP }
        ( is_authorized, redirect_url, message ) = self.helper.check_if_authorized(shib_dct)
        self.assertEqual( True, is_authorized )
        self.assertEqual( '', redirect_url )
        self.assertEqual( '', message )

    # end class LoginHelper_Test
