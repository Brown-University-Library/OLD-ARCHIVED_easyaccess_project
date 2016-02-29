# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random

from article_request_app import settings_app


log = logging.getLogger('access')


class ShibChecker( object ):
    """ Contains helpers for checking Shib. """

    def __init__( self ):
        self.TEST_SHIB_JSON = settings_app.DEVELOPMENT_SHIB_DCT
        # self.SHIB_ERESOURCE_PERMISSION = os.environ['EZRQST__SHIB_ERESOURCE_PERMISSION']

    def grab_shib_info( self, request ):
        """ Grabs shib values from http-header or dev-settings.
            Called by LoginHelper.grab_user_info() """
        shib_dct = {}
        if 'Shibboleth-eppn' in request.META:
            shib_dct = self.grab_shib_from_meta( request )
        else:
            if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:
                shib_dct = json.loads( self.TEST_SHIB_JSON )
        log.debug( 'in models.ShibChecker.grab_shib_info(); shib_dct is: %s' % pprint.pformat(shib_dct) )
        return shib_dct

    def grab_shib_from_meta( self, request ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dct = {
            'brown_status': request.META.get( 'Shibboleth-brownStatus', '' ),  # eg. 'active'
            'brown_type': request.META.get( 'Shibboleth-brownType', '' ),  # eg. 'Staff'
            'department': request.META.get( 'Shibboleth-department', '' ),
            'edu_person_primary_affiliation': request.META.get( 'Shibboleth-eduPersonPrimaryAffiliation', '' ),  # eg. 'staff'
            'email': request.META.get( 'Shibboleth-mail', '' ).lower(),
            'eppn': request.META.get( 'Shibboleth-eppn', '' ),
            'id_net': request.META.get( 'Shibboleth-brownNetId', '' ),
            'id_short': request.META.get( 'Shibboleth-brownShortId', '' ),
            'member_of': request.META.get( 'Shibboleth-isMemberOf', '' ).split(';'),  # only dct element that's not a unicode string
            'name_first': request.META.get( 'Shibboleth-givenName', '' ),
            'name_last': request.META.get( 'Shibboleth-sn', '' ),
            'patron_barcode': request.META.get( 'Shibboleth-brownBarCode', '' ),
            'phone': request.META.get( 'Shibboleth-phone', '' ),  # valid?
            'title': request.META.get( 'Shibboleth-title', '' ),
            }
        return shib_dct

    # def evaluate_shib_info( self, shib_dct ):
    #     """ Returns boolean.
    #         Called by models.ShibViewHelper.check_shib_headers() """
    #     validity = False
    #     if self.all_values_present(shib_dct) and self.brown_user_confirmed(shib_dct) and self.authorized(shib_dct['patron_barcode']):
    #         validity = True
    #     log.debug( 'validity, `%s`' % validity )
    #     return validity

    # def all_values_present( self, shib_dct ):
    #     """ Returns boolean.
    #         Called by evaluate_shib_info() """
    #     present_check = False
    #     if sorted( shib_dct.keys() ) == ['email', 'eppn', 'firstname', 'lastname', 'member_of', 'patron_barcode']:
    #         value_test = 'init'
    #         for (key, value) in shib_dct.items():
    #             if len( value.strip() ) == 0:
    #                 value_test = 'fail'
    #         if value_test == 'init':
    #             present_check = True
    #     log.debug( 'in models.ShibChecker.all_values_present(); present_check, `%s`' % present_check )
    #     return present_check

    # def brown_user_confirmed( self, shib_dct ):
    #     """ Returns boolean.
    #         Called by evaluate_shib_info() """
    #     brown_check = False
    #     if '@brown.edu' in shib_dct['eppn']:
    #         brown_check = True
    #     log.debug( 'in models.ShibChecker.brown_user_confirmed(); brown_check, `%s`' % brown_check )
    #     return brown_check

    # def authorized( self, patron_barcode ):
    #     """ Returns boolean.
    #         Called by evaluate_shib_info() """
    #     authZ_check = False
    #     papi_helper = PatronApiHelper( patron_barcode )
    #     if papi_helper.ptype_validity is True:
    #         authZ_check = True
    #     log.debug( 'authZ_check, `%s`' % authZ_check )
    #     return authZ_check

    # end class ShibChecker


