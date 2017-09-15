# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
# from .shib_helper import ShibChecker
from common_classes.shib_helper import ShibChecker
from article_request_app import settings_app
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote


log = logging.getLogger('access')
shib_checker = ShibChecker()


class LoginHelper( object ):
    """ Contains helpers for views.login_handler() """

    def __init__( self, log_id='not_set' ):
        self.log_id = log_id
        self.denied_permission_message = '''
It appears you are not authorized to use interlibrary-loan services, which are for the use of faculty, staff, and students.

If you believe you should be permitted to use interlibrary-loan services, please contact the circulation staff at the Rockefeller Library, or call them at {phone}, or email them at {email}, and they'll help you.
'''.format( phone=settings_app.PERMISSION_DENIED_PHONE, email=settings_app.PERMISSION_DENIED_EMAIL )

    # def check_referrer( self, session_dct, meta_dct ):
    #     """ Ensures request came from '/find/' or a login redirect.
    #         Called by views.login_handler() """
    #     ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
    #     log.debug( 'last_path, `{}`'.format(last_path) )
    #     if last_path == '/easyaccess/find/' or last_path == '/easyaccess/article_request/login_helper/':
    #         referrer_ok = True
    #     if referrer_ok is False:
    #         redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
    #     log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
    #     return ( referrer_ok, redirect_url )

    def grab_user_info( self, request, localdev ):
        """ Updates session with real-shib or development-shib info.
            Called by views.login_handler() """
        # if localdev is False and shib_status == 'will_force_login':
        log.debug( 'localdev, `{}`'.format(localdev) )
        if localdev is False:
            shib_dct = shib_checker.grab_shib_info( request.META, request.get_host() )
        else:  # localdev
            shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        request.session['user_json'] = json.dumps( shib_dct )
        log.debug( 'shib_dct, `%s`' % pprint.pformat(shib_dct) )
        return shib_dct

    def check_if_authorized( self, shib_dct ):
        """ Checks whether user is authorized to request article.
            Called by views.login_handler() """
        log.debug( '`{id}` checking authorization'.format(id=self.log_id) )
        # ( is_authorized, redirect_url, message ) = ( False, reverse('article_request:message_url'), self.denied_permission_message )
        ( is_authorized, redirect_url, message ) = ( False, reverse('article_request:shib_logout_url'), self.denied_permission_message )
        if settings_app.REQUIRED_GROUPER_GROUP in shib_dct.get( 'member_of', '' ):
            log.debug( '`{id}` user authorized'.format(id=self.log_id) )
            ( is_authorized, redirect_url, message ) = ( True, '', '' )
        log.debug( '`{id}` is_authorized, `{auth}`; redirect_url, `{url}`; message, ```{msg}```'.format(id=self.log_id, auth=is_authorized, url=redirect_url, msg=message) )
        return ( is_authorized, redirect_url, message )

    def update_session( self, request ):
        """ Updates necessary session attributes.
            Called by views.login_handler() """
        request.session['illiad_login_check_flag'] = 'good'
        request.session['findit_illiad_check_flag'] = ''
        request.session['findit_illiad_check_enhanced_querystring'] = ''
        # request.session['shib_status'] = ''
        return

    # end class LoginHelper
