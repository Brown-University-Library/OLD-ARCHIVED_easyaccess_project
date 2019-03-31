# # -*- coding: utf-8 -*-

# from __future__ import unicode_literals

# import logging, os, pprint, random
# from types import NoneType
# from common_classes import settings_common_tests as settings_app
# from common_classes.illiad_helper import IlliadHelper
# from django.test import Client, TestCase


# log = logging.getLogger( 'access' )
# TestCase.maxDiff = None


# class IlliadHelperTest( TestCase ):
#     """ Tests common_classes.illiad_helper.IlliadHelper() """

#     def setUp(self):
#         self.helper = IlliadHelper()
#         self.illiad_session_instance = None

#     ### connect() test ###

#     def test_connect(self):
#         """ Connect should instantiate illiad_session_instance object.
#             Does not yet contact ILLiad (login does), so object is same whether user is good, new, blocked, or disavowed. """
#         ill_username = settings_app.TEST_ILLIAD_GOOD_USERNAME
#         ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
#         self.illiad_session_instance = illiad_session_instance
#         self.assertEqual(
#             ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
#             sorted(illiad_session_instance.__dict__.keys()) )
#         self.assertEqual( False, illiad_session_instance.blocked_patron )
#         self.assertEqual( False, illiad_session_instance.registered )
#         self.assertEqual( None, illiad_session_instance.session_id )
#         self.assertEqual( settings_app.TEST_ILLIAD_GOOD_USERNAME, illiad_session_instance.username )
#         self.assertEqual( True, ok )

#     ### login() tests ###

#     def test_login__good_user(self):
#         """ Good-user login should show user is authenticated, and is registered. """
#         ill_username = settings_app.TEST_ILLIAD_GOOD_USERNAME
#         ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
#         self.illiad_session_instance = illiad_session_instance
#         ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )
#         ## instance checks
#         self.assertEqual(
#             ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
#             sorted(illiad_session_instance.__dict__.keys()) )
#         self.assertEqual( False, illiad_session_instance.blocked_patron )
#         self.assertEqual( True, illiad_session_instance.registered )
#         self.assertEqual( 11, len(illiad_session_instance.session_id) )
#         self.assertEqual( settings_app.TEST_ILLIAD_GOOD_USERNAME, illiad_session_instance.username )
#         ## login_dct checks
#         self.assertEqual(
#             ['authenticated', 'new_user', 'registered', 'session_id'],
#             sorted(login_dct.keys()) )
#         self.assertEqual( True, login_dct['authenticated'])
#         self.assertEqual( False, login_dct['new_user'])
#         self.assertEqual( True, login_dct['registered'])
#         self.assertEqual( illiad_session_instance.session_id, login_dct['session_id'])
#         ## ok check
#         self.assertEqual( True, ok )

#     # def test_login__new_user(self):
#     #     """ New-user login should show user is authenticated, but is not registered.
#     #         Test is good, but disabled so as not to unnecessarily create lots of new users. """
#     #     ill_username = '{test_root}{random}'.format( test_root=settings_app.TEST_ILLIAD_NEW_USER_ROOT, random=random.randint(11111, 99999) )
#     #     ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
#     #     self.illiad_session_instance = illiad_session_instance
#     #     ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )
#     #     ## instance checks
#     #     self.assertEqual(
#     #         ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
#     #         sorted(illiad_session_instance.__dict__.keys()) )
#     #     self.assertEqual( False, illiad_session_instance.blocked_patron )
#     #     self.assertEqual( False, illiad_session_instance.registered )
#     #     self.assertEqual( 11, len(illiad_session_instance.session_id) )
#     #     self.assertEqual( ill_username, illiad_session_instance.username )
#     #     ## login_dct checks
#     #     self.assertEqual(
#     #         ['authenticated', 'new_user', 'registered', 'session_id'],
#     #         sorted(login_dct.keys()) )
#     #     self.assertEqual( True, login_dct['authenticated'])
#     #     self.assertEqual( False, login_dct['new_user'])  # TODO: check this out sometime in the library; seems it should return True in this case
#     #     self.assertEqual( False, login_dct['registered'])
#     #     self.assertEqual( illiad_session_instance.session_id, login_dct['session_id'])
#     #     ## ok check
#     #     self.assertEqual( True, ok )

#     ## test disabled due to blocked no longer being detected on login -- but on getting the intial form before it is submitted
#     ## module will need to be re-worked
#     # def test_login__blocked_user(self):
#     #     """ Blocked-user login should show user is not authenticated, is registered, and is blocked. """
#     #     ill_username = settings_app.TEST_ILLIAD_BLOCKED_USERNAME
#     #     ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
#     #     self.illiad_session_instance = illiad_session_instance
#     #     ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )

#     #     log.debug( 'illiad_session_instance, ```%s```' % pprint.pformat(illiad_session_instance.__dict__) )
#     #     log.debug( 'login_dct, ```%s```' % pprint.pformat(login_dct) )
#     #     log.debug( 'ok, ```%s```' % ok )

#     #     ## instance checks
#     #     self.assertEqual(
#     #         ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
#     #         sorted(illiad_session_instance.__dict__.keys()) )
#     #     self.assertEqual( True, illiad_session_instance.blocked_patron )
#     #     self.assertEqual( True, illiad_session_instance.registered )
#     #     self.assertEqual( None, illiad_session_instance.session_id )
#     #     self.assertEqual( settings_app.TEST_ILLIAD_BLOCKED_USERNAME, illiad_session_instance.username )
#     #     ## login_dct checks
#     #     self.assertEqual(
#     #         ['authenticated', 'blocked', 'new_user', 'session_id'],
#     #         sorted(login_dct.keys()) )
#     #     self.assertEqual( False, login_dct['authenticated'])
#     #     self.assertEqual( True, login_dct['blocked'])
#     #     self.assertEqual( False, login_dct['new_user'])
#     #     self.assertEqual( None, login_dct['session_id'])
#     #     ## ok check
#     #     self.assertEqual( True, ok )

#     def test_login__disavowed_user(self):
#         """ Disavowed-user login should just fail. """
#         ill_username = settings_app.TEST_ILLIAD_DISAVOWED_USERNAME
#         ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
#         self.illiad_session_instance = illiad_session_instance
#         ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )
#         ## instance checks
#         self.assertEqual( None, illiad_session_instance )
#         ## login_dct checks
#         self.assertEqual( None, login_dct )
#         ## ok check
#         self.assertEqual( False, ok )

#     ### register_new_user() test ###

#     # def test_register_new_user(self):
#     #     """ New user registration should succeed, such that a subsequent attempted login should indicate a status of registered.
#     #         Test is good, but disabled so as not to unnecessarily create lots of new users. """
#     #     ill_username = '{test_root}{random}'.format( test_root=settings_app.TEST_ILLIAD_NEW_USER_ROOT, random=random.randint(11111, 99999) )
#     #     ( illiad_session_instance, ok ) = self.helper.connect( ill_username )
#     #     self.illiad_session_instance = illiad_session_instance
#     #     ( illiad_session_instance, login_dct, ok ) = self.helper.login( illiad_session_instance )
#     #     self.assertEqual( False, illiad_session_instance.registered )
#     #     user_dct = {
#     #         'eppn': '{}@brown.edu'.format(ill_username),
#     #         'name_first': 'test_firstname',
#     #         'name_last': 'test_lastname',
#     #         'email': 'test@test.edu',
#     #         'brown_type': 'test_brown_type',
#     #         'phone': 'test_phone',
#     #         'department': 'test_department'
#     #         }
#     #     ok = self.helper.register_new_user( illiad_session_instance, user_dct )
#     #     self.assertEqual( True, ok )
#     #     ###
#     #     ## try subsequent login, with checks identical to test_login__good_user()
#     #     ###
#     #     new_helper = IlliadHelper()
#     #     ( illiad_session_instance, ok ) = new_helper.connect( ill_username )
#     #     self.illiad_session_instance = illiad_session_instance
#     #     ( illiad_session_instance, login_dct, ok ) = new_helper.login( illiad_session_instance )
#     #     ## instance checks
#     #     self.assertEqual(
#     #         ['auth_header', 'blocked_patron', 'cookies', 'header', 'registered', 'session_id', 'url', 'username'],
#     #         sorted(illiad_session_instance.__dict__.keys()) )
#     #     self.assertEqual( False, illiad_session_instance.blocked_patron )
#     #     self.assertEqual( True, illiad_session_instance.registered )
#     #     self.assertEqual( 11, len(illiad_session_instance.session_id) )
#     #     self.assertEqual( ill_username, illiad_session_instance.username )
#     #     ## login_dct checks
#     #     self.assertEqual(
#     #         ['authenticated', 'new_user', 'registered', 'session_id'],
#     #         sorted(login_dct.keys()) )
#     #     self.assertEqual( True, login_dct['authenticated'])
#     #     self.assertEqual( False, login_dct['new_user'])
#     #     self.assertEqual( True, login_dct['registered'])
#     #     self.assertEqual( illiad_session_instance.session_id, login_dct['session_id'])
#     #     ## ok check
#     #     self.assertEqual( True, ok )
#     #     ## logout
#     #     new_helper.logout_user( self.illiad_session_instance )

#     def tearDown(self):
#         self.helper.logout_user( self.illiad_session_instance )

#     # end class IlliadHelperTest()
