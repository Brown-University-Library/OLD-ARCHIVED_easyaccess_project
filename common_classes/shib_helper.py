# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from article_request_app import settings_app
from django.conf import settings as project_settings


log = logging.getLogger('access')


class ShibChecker( object ):
    """ Contains helpers for checking Shib.
        Called by `article_request_app/classes/login_helper.py`
                  `delivery/classes/login_helper.py` """

    def grab_shib_info( self, meta_dct, host ):
        """ Grabs shib values from http-header or dev-settings.
            Called by: article_request_app/classes/login_helper.LoginHelper.grab_user_info()
                       delivery/classes/login_helper.LoginViewHelper.update_user() """
        shib_dct = {}
        if project_settings.SHIB_EPPN_KEY in meta_dct:
            shib_dct = self.grab_shib_from_meta( meta_dct )
        else:
            if host == '127.0.0.1' and project_settings.DEBUG == True:
                shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        log.debug( 'in models.ShibChecker.grab_shib_info(); shib_dct is: %s' % pprint.pformat(shib_dct) )
        return shib_dct

    def grab_shib_from_meta( self, meta_dct ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dct = {
            'brown_status': meta_dct.get( 'Shibboleth-brownStatus', '' ),  # eg. 'active'
            'brown_type': meta_dct.get( 'Shibboleth-brownType', '' ),  # eg. 'Staff'
            'department': meta_dct.get( 'Shibboleth-department', '' ),
            'edu_person_primary_affiliation': meta_dct.get( 'Shibboleth-eduPersonPrimaryAffiliation', '' ),  # eg. 'staff'
            'email': meta_dct.get( 'Shibboleth-mail', '' ).lower(),
            'eppn': meta_dct.get( 'Shibboleth-eppn', '' ),
            'id_net': meta_dct.get( 'Shibboleth-brownNetId', '' ),
            'id_short': meta_dct.get( 'Shibboleth-brownShortId', '' ),
            'member_of': sorted( meta_dct.get('Shibboleth-isMemberOf', '').split(';') ),  # only dct element that's not a unicode string
            'name_first': meta_dct.get( 'Shibboleth-givenName', '' ),
            'name_last': meta_dct.get( 'Shibboleth-sn', '' ),
            'patron_barcode': meta_dct.get( 'Shibboleth-brownBarCode', '' ),
            'phone': meta_dct.get( 'Shibboleth-phone', 'unavailable' ),  # valid?
            'title': meta_dct.get( 'Shibboleth-title', '' ),
            }
        return shib_dct

    # end class ShibChecker


