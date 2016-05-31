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
    """ Contains helpers for views.login() """

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from '/find/' or a login redirect.
            Called by views.login_handler() """
        ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
        log.debug( 'last_path, `{}`'.format(last_path) )
        if last_path == '/easyaccess/find/' or last_path == '/easyaccess/article_request/login_helper/':
            referrer_ok = True
        if referrer_ok is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
        return ( referrer_ok, redirect_url )

    # def build_shib_redirect_url( self, shib_status, scheme, host, session_dct, meta_dct ):
    #     """ Builds shib-redirect login or logout url.
    #         Called by views.login() """
    #     if shib_status == '':  # clean entry: builds logout url
    #         redirect_tuple = self._make_force_logout_redirect_url( scheme, host, session_dct )
    #     elif shib_status == 'will_force_logout':  # logout occurred; builds login url
    #         redirect_tuple = self._make_force_login_redirect_url( scheme, host, session_dct )
    #     elif shib_status == 'will_force_login' and meta_dct.get('Shibboleth-eppn', '') == '':  # also builds logout url, like first condition
    #         redirect_tuple = self._make_force_logout_redirect_url( scheme, host, session_dct )
    #     log.debug( 'redirect_tuple, `{}`'.format(redirect_tuple) )
    #     return redirect_tuple

    # def _make_force_logout_redirect_url( self, scheme, host, session_dct ):
    #     """ Builds logout-redirect url
    #         Called by build_shib_redirect_url() """
    #     updated_shib_status = 'will_force_logout'
    #     app_login_url = '%s://%s%s?%s' % ( scheme, host, reverse('article_request:login_url'), session_dct['login_openurl'] )  # app_login_url isn't the shib url; it's the url to this login-app
    #     log.debug( 'app_login_url, `%s`' % app_login_url )
    #     encoded_app_login_url = urlquote( app_login_url )  # django's urlquote()
    #     force_logout_redirect_url = '%s?return=%s' % ( settings_app.SHIB_LOGOUT_URL_ROOT, encoded_app_login_url )
    #     redirect_tuple = ( force_logout_redirect_url, updated_shib_status )
    #     log.debug( 'redirect_tuple, `{}`'.format(redirect_tuple) )
    #     return redirect_tuple

    # def _make_force_login_redirect_url( self, scheme, host, session_dct ):
    #     """ Builds login-redirect url
    #         Called by build_shib_redirect_url()
    #         Note, fyi, normally a shib httpd.conf entry triggers login via a config line like `require valid-user`.
    #             This SHIB_LOGIN_URL setting, though, is a url like: `https://host/shib.sso/login?target=/this_url_path`
    #             ...so it's that shib.sso/login url that triggers the login, not this app login url.
    #             This app login url _is_ shib-configured, though to perceive shib headers if they exist. """
    #     updated_shib_status = 'will_force_login'
    #     encoded_openurl = urlquote( session_dct['login_openurl'] )
    #     force_login_redirect_url = '%s?%s' % ( settings_app.SHIB_LOGIN_URL, encoded_openurl )
    #     redirect_tuple = ( force_login_redirect_url, updated_shib_status )
    #     log.debug( 'redirect_tuple, `{}`'.format(redirect_tuple) )
    #     return redirect_tuple

    def grab_user_info( self, request, localdev ):
        """ Updates session with real-shib or development-shib info.
            Called by views.login() """
        # if localdev is False and shib_status == 'will_force_login':
        log.debug( 'localdev, `{}`'.format(localdev) )
        if localdev is False:
            shib_dct = shib_checker.grab_shib_info( request.META, request.get_host() )
        else:  # localdev
            shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        request.session['user_json'] = json.dumps( shib_dct )
        log.debug( 'shib_dct, `%s`' % pprint.pformat(shib_dct) )
        return shib_dct

    # def grab_user_info( self, request, localdev, shib_status ):
    #     """ Updates session with real-shib or development-shib info.
    #         Called by views.login() """
    #     # if localdev is False and shib_status == 'will_force_login':
    #     if localdev is False:
    #         request.session['shib_status'] = ''
    #         shib_dct = shib_checker.grab_shib_info( request.META, request.get_host() )
    #     else:  # localdev
    #         shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
    #     request.session['user_json'] = json.dumps( shib_dct )
    #     log.debug( 'shib_dct, `%s`' % pprint.pformat(shib_dct) )
    #     return shib_dct

    def update_session( self, request ):
        """ Updates necessary session attributes.
            Called by views.login() """
        request.session['illiad_login_check_flag'] = 'good'
        request.session['findit_illiad_check_flag'] = ''
        request.session['findit_illiad_check_enhanced_querystring'] = ''
        # request.session['shib_status'] = ''
        return

    # end class LoginHelper
