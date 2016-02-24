# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random

from article_request_app import settings_app


log = logging.getLogger('access')


# class ShibViewHelper( object ):
#     """ Contains helpers for views.check_login() and views.login() """

#     def check_shib_existance( self, request ):
#         """ Grabs and checks shib headers, returns boolean.
#             Called by views.check_login() """
#         shib_checker = ShibChecker()
#         shib_dict = shib_checker.grab_shib_info( request )
#         log.debug( 'returning shib validity `%s`' % validity )
#         return ( validity, shib_dict )

#     def check_shib_headers( self, request ):
#         """ Grabs and checks shib headers, returns boolean.
#             Called by views.login() """
#         shib_checker = ShibChecker()
#         shib_dict = shib_checker.grab_shib_info( request )
#         validity = shib_checker.evaluate_shib_info( shib_dict )
#         log.debug( 'returning shib validity `%s`' % validity )
#         return ( validity, shib_dict )

#     def prep_login_redirect( self, request ):
#         """ Prepares redirect response-object to views.oops() on bad authZ (p-type problem).
#             Called by views.shib_login() """
#         request.session['shib_login_error'] = 'Problem on authorization.'
#         request.session['shib_authorized'] = False
#         redirect_url = '%s?bibnum=%s&barcode=%s' % ( reverse('login_url'), request.session['item_bib'], request.session['item_barcode'] )
#         log.debug( 'ShibViewHelper redirect_url, `%s`' % redirect_url )
#         resp = HttpResponseRedirect( redirect_url )
#         return resp

#     def build_response( self, request, shib_dict ):
#         """ Sets session vars and redirects to the hidden processor page.
#             Called by views.shib_login() """
#         log.debug( 'starting ShibViewHelper.build_response()' )
#         self.update_session( request, shib_dict )
#         scheme = 'https' if request.is_secure() else 'http'
#         redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse('processor_url') )
#         log.debug( 'leaving ShibViewHelper; redirect_url `%s`' % redirect_url )
#         return_response = HttpResponseRedirect( redirect_url )
#         log.debug( 'returning shib response' )
#         return return_response

#     def update_session( self, request, shib_dict ):
#         """ Updates session with shib info.
#             Called by build_response() """
#         request.session['shib_login_error'] = False
#         request.session['shib_authorized'] = True
#         request.session['user_full_name'] = '%s %s' % ( shib_dict['firstname'], shib_dict['lastname'] )
#         request.session['user_last_name'] = shib_dict['lastname']
#         request.session['user_email'] = shib_dict['email']
#         request.session['shib_login_error'] = False
#         request.session['josiah_api_name'] = shib_dict['firstname']
#         request.session['josiah_api_barcode'] = shib_dict['patron_barcode']
#         log.debug( 'ShibViewHelper.update_session() completed' )
#         return

#     # end class ShibViewHelper


class ShibChecker( object ):
    """ Contains helpers for checking Shib.
        Called by ShibViewHelper """

    def __init__( self ):
        self.TEST_SHIB_JSON = settings_app.DEVELOPMENT_SHIB_DCT
        # self.SHIB_ERESOURCE_PERMISSION = os.environ['EZRQST__SHIB_ERESOURCE_PERMISSION']

    def grab_shib_info( self, request ):
        """ Grabs shib values from http-header or dev-settings.
            Called by models.ShibViewHelper.check_shib_headers() """
        shib_dict = {}
        if 'Shibboleth-eppn' in request.META:
            shib_dict = self.grab_shib_from_meta( request )
        else:
            if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:
                shib_dict = json.loads( self.TEST_SHIB_JSON )
        log.debug( 'in models.ShibChecker.grab_shib_info(); shib_dict is: %s' % pprint.pformat(shib_dict) )
        return shib_dict

    def grab_shib_from_meta( self, request ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dict = {
            'eppn': request.META.get( 'Shibboleth-eppn', '' ),
            'firstname': request.META.get( 'Shibboleth-givenName', '' ),
            'lastname': request.META.get( 'Shibboleth-sn', '' ),
            'email': request.META.get( 'Shibboleth-mail', '' ).lower(),
            'patron_barcode': request.META.get( 'Shibboleth-brownBarCode', '' ),
            'member_of': request.META.get( 'Shibboleth-isMemberOf', '' ) }
        return shib_dict

    def evaluate_shib_info( self, shib_dict ):
        """ Returns boolean.
            Called by models.ShibViewHelper.check_shib_headers() """
        validity = False
        if self.all_values_present(shib_dict) and self.brown_user_confirmed(shib_dict) and self.authorized(shib_dict['patron_barcode']):
            validity = True
        log.debug( 'in models.ShibChecker.evaluate_shib_info(); validity, `%s`' % validity )
        return validity

    def all_values_present( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        present_check = False
        if sorted( shib_dict.keys() ) == ['email', 'eppn', 'firstname', 'lastname', 'member_of', 'patron_barcode']:
            value_test = 'init'
            for (key, value) in shib_dict.items():
                if len( value.strip() ) == 0:
                    value_test = 'fail'
            if value_test == 'init':
                present_check = True
        log.debug( 'in models.ShibChecker.all_values_present(); present_check, `%s`' % present_check )
        return present_check

    def brown_user_confirmed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        brown_check = False
        if '@brown.edu' in shib_dict['eppn']:
            brown_check = True
        log.debug( 'in models.ShibChecker.brown_user_confirmed(); brown_check, `%s`' % brown_check )
        return brown_check

    def authorized( self, patron_barcode ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        authZ_check = False
        papi_helper = PatronApiHelper( patron_barcode )
        if papi_helper.ptype_validity is True:
            authZ_check = True
        log.debug( 'authZ_check, `%s`' % authZ_check )
        return authZ_check

    # end class ShibChecker


