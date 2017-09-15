# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from article_request_app import settings_app
from django.conf import settings as project_settings


log = logging.getLogger('access')


def build_shib_login_url( ):
    """ Builds a shib Service-Provider login url.
        This url is to the server Service-Provider login url, with a `?target=` parameter that lets shib know where to redirect the user.
        Called by: article_request_app.views.shib_login() """


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
            'brown_status': meta_dct.get( project_settings.SHIB_STATUS_KEY, '' ),  # eg. 'active'
            'brown_type': meta_dct.get( project_settings.SHIB_TYPE_KEY, '' ),  # eg. 'Staff'
            'department': meta_dct.get( project_settings.SHIB_DEPARTMENT_KEY, '' ),
            'edu_person_primary_affiliation': meta_dct.get( project_settings.SHIB_AFFILIATIONPRIMARY_KEY, '' ),  # eg. 'staff'
            'email': meta_dct.get( project_settings.SHIB_MAIL_KEY, '' ).lower(),
            'eppn': meta_dct.get( project_settings.SHIB_EPPN_KEY, '' ),
            'id_net': meta_dct.get( project_settings.SHIB_NETID_KEY, '' ),
            'id_short': meta_dct.get( project_settings.SHIB_SHORTID_KEY, '' ),
            'member_of': sorted( meta_dct.get(project_settings.SHIB_MEMBEROF_KEY, '').split(';') ),  # only dct element that's not a unicode string
            'name_first': meta_dct.get( project_settings.SHIB_NAMEFIRST_KEY, '' ),
            'name_last': meta_dct.get( project_settings.SHIB_NAMELAST_KEY, '' ),
            'patron_barcode': meta_dct.get( project_settings.SHIB_BARCODE_KEY, '' ),
            'phone': meta_dct.get( project_settings.SHIB_PHONE_KEY, 'unavailable' ),  # valid?
            'title': meta_dct.get( project_settings.SHIB_TITLE_KEY, '' ),
            }
        return shib_dct

    # end class ShibChecker
