# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from .shib_helper import ShibChecker
from article_request_app import settings_app
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote


log = logging.getLogger('access')
shib_checker = ShibChecker()


class LoginHelper( object ):
    """ Contains helpers for views.login() """

    def check_referrer( self, request ):
        """ Ensures request came from findit app.
            Called by views.login() """
        findit_check = False
        findit_illiad_check_flag = request.session.get( 'findit_illiad_check_flag', '' )
        findit_illiad_check_openurl = request.session.get( 'findit_illiad_check_openurl', '' )
        if findit_illiad_check_flag == 'good' and findit_illiad_check_openurl == request.META.get('QUERY_STRING', ''):
            findit_check = True
        log.debug( 'findit_check, `%s`' % findit_check )
        if findit_check is True:
            request.session['login_openurl'] = request.META.get('QUERY_STRING', '')
        elif findit_check is not True:
            log.warning( 'Bad attempt from source-url, ```%s```; ip, `%s`' % (
                request.META.get('HTTP_REFERER', ''), request.META.get('REMOTE_ADDR', '') ) )
        return findit_check

    def assess_status( self, request ):
        """ Assesses localdev status and shib_status.
            Called by views.login() """
        localdev = False
        shib_status = request.session.get( 'shib_status', '' )
        if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
            localdev = True
        log.debug( 'localdev, `%s`; shib_status, `%s`' % (localdev, shib_status) )
        return ( localdev, shib_status )

    def make_force_logout_redirect_url( self, request ):
        """ Builds logout-redirect url
            Called by views.login() """
        request.session['shib_status'] = 'will_force_logout'
        login_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:login_url'), request.session['login_openurl'] )  # for logout and login redirections
        log.debug( 'login_url, `%s`' % login_url )
        encoded_login_url = urlquote( login_url )  # django's urlquote()
        force_logout_redirect_url = '%s?return=%s' % ( settings_app.SHIB_LOGOUT_URL_ROOT, encoded_login_url )
        log.debug( 'force_logout_redirect_url, `%s`' % force_logout_redirect_url )
        return force_logout_redirect_url

    def make_force_login_redirect_url( self, request ):
        """ Builds login-redirect url
            Called by views.login()
            Note, fyi, normally a shib httpd.conf entry triggers login via a config line like `require valid-user`.
                This SHIB_LOGIN_URL setting, though, is a url like: `https://host/shib.sso/login?target=/this_url_path`
                ...so it's that shib.sso/login url that triggers the login, not this app login url.
                This app login url _is_ shib-configured, though to perceive shib headers if they exist. """
        request.session['shib_status'] = 'will_force_login'
        encoded_openurl = urlquote( request.session['login_openurl'] )
        force_login_redirect_url = '%s?%s' % ( settings_app.SHIB_LOGIN_URL, encoded_openurl )
        log.debug( 'force_login_redirect_url, `%s`' % force_login_redirect_url )
        return force_login_redirect_url

    def grab_user_info( self, request, localdev, shib_status ):
        """ Updates session with real-shib or development-shib info.
            Called by views.login() """
        if localdev is False and shib_status == 'will_force_login':
            request.session['shib_status'] = ''
            shib_dct = shib_checker.grab_shib_info( request )
        else:  # localdev
            shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        request.session['user'] = json.dumps( shib_dct )
        log.debug( 'shib_dct, `%s`' % pprint.pformat(shib_dct) )
        return shib_dct

    def update_session( self, request ):
        """ Updates necessary session attributes.
            Called by views.login() """
        request.session['illiad_login_check_flag'] = 'good'
        request.session['findit_illiad_check_flag'] = ''
        request.session['findit_illiad_check_openurl'] = ''
        # request.session['shib_status'] = ''
        return

    # end class LoginHelper
