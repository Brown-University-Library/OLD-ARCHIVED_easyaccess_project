# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from common_classes.shib_helper import ShibChecker
from delivery import app_settings as settings_app
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote


log = logging.getLogger('access')
shib_checker = ShibChecker()


class LoginViewHelper(object):
    """ Contains helpers for views.login_handler() """

    def __init__(self):
        pass

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /availability/.
            Called by views.login_handler() """
        ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
        log.debug( 'last_path, `{}`'.format(session_dct.get('last_path', '')) )
        if last_path == '/easyaccess/borrow/availability/':
            referrer_ok = True
        if referrer_ok is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
        return ( referrer_ok, redirect_url )

    def update_user( self, localdev, meta_dct, host ):
        """ For now just returns shib_dct, with courses removed to make it shorter (it'll be jsonized into the session);
            eventually with create or update a user object and return that.
            Called by views.login_handler() """
        log.debug( 'localdev, `{}`'.format(localdev) )
        if localdev is False:
            ( shib_dct, filtered_memberships ) = ( shib_checker.grab_shib_info(meta_dct, host), [] )
            memberships = shib_dct['member_of']
            for membership in memberships:
                log.debug( 'membership[0:7], `{}`'.format(membership[0:7]) )
                if membership[0:7] != 'COURSE:':
                    filtered_memberships.append( membership )
            log.debug( 'filtered_memberships, ```{}```'.format(pprint.pformat(filtered_memberships)) )
            shib_dct['member_of'] = filtered_memberships
        else:  # localdev
            shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        log.debug( 'shib_dct, `%s`' % pprint.pformat(shib_dct) )
        return shib_dct

    # end class LoginViewHelper()


# class LoginViewHelper(object):
#     """ Contains helpers for views.login_handler() """

#     def __init__(self):
#         pass

#     # def check_referrer( self, session_dct, meta_dct ):
#     #     """ Ensures request came from /availability/.
#     #         Called by views.login_handler() """
#     #     ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
#     #     if last_path == '/easyaccess/borrow/availability/':
#     #         referrer_ok = True
#     #     elif shib_status in ['will_force_logout', 'will_force_login']:
#     #         referrer_ok = True
#     #     if referrer_ok is False:
#     #         redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
#     #     log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
#     #     return ( referrer_ok, redirect_url )

#     def check_referrer( self, session_dct, meta_dct ):
#         """ Ensures request came from /availability/.
#             Called by views.login_handler() """
#         ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
#         log.debug( 'last_path, `{}`'.format(session_dct.get('last_path', '')) )
#         if last_path == '/easyaccess/borrow/availability/':
#             referrer_ok = True
#         if referrer_ok is False:
#             redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
#         log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
#         return ( referrer_ok, redirect_url )

#     # def assess_shib_redirect_need( self, session, host, meta_dct ):
#     #     """ Determines whether a shib-redirect login or logout url is needed.
#     #         Returns needed-boolean, and extracted/updated shib_status.
#     #         Called by views.login()
#     #         `shib_status` flow:
#     #         - '', from a new-request, will be changed to 'will_force_logout' and trigger a shib-logout redirect
#     #         - 'will_force_logout' will be changed to 'will_force_login' and trigger a shib-login redirect
#     #         - 'will_force_login' is usually ok, and the session should contain shib info, but if not, a logout-login will be triggered
#     #         TODO: figure out why settings.DEBUG is getting changed unexpectedly and fix it. """
#     #     ( localdev_check, redirect_check, shib_status ) = ( False, False, session.get('shib_status', '') )
#     #     log.debug( 'initial shib_status, `{}`'.format(shib_status) )
#     #     log.debug( 'meta_dct, ```{}```'.format(pprint.pformat(meta_dct)) )
#     #     if host == '127.0.0.1' and project_settings.DEBUG2 == True:  # eases local development
#     #         localdev_check = True
#     #     else:
#     #         if shib_status == '' or shib_status == 'will_force_logout':
#     #             redirect_check = True
#     #         elif shib_status == 'will_force_login' and meta_dct.get('Shibboleth-eppn', '') == '':
#     #             ( redirect_check, shib_status ) = ( True, 'will_force_logout' )
#     #     assessment_tuple = ( localdev_check, redirect_check, shib_status )
#     #     log.debug( 'assessment_tuple (localdev_check, redirect_check, shib_status), `{}`'.format(assessment_tuple) )
#     #     return assessment_tuple

#     # def build_shib_redirect_url( self, shib_status, scheme, host, session_dct, meta_dct ):
#     #     """ Builds shib-redirect login or logout url.
#     #         Called by views.login() """
#     #     if shib_status == '':  # clean entry: builds logout url
#     #         redirect_tuple = self._make_force_logout_redirect_url( scheme, host, session_dct )
#     #     elif shib_status == 'will_force_logout':  # logout occurred; builds login url
#     #         redirect_tuple = self._make_force_login_redirect_url( scheme, host, session_dct )
#     #     elif shib_status == 'will_force_login' and meta_dct.get('Shibboleth-eppn', '') == '':  # also builds logout url, like first condition
#     #         redirect_tuple = self._make_force_logout_redirect_url( scheme, host, session_dct )
#     #     log.debug( 'redirect_tuple, `{}`'.format(redirect_tuple) )
#     #     return redirect_tuple

#     # def _make_force_logout_redirect_url( self, scheme, host, session_dct ):
#     #     """ Builds logout-redirect url
#     #         Called by build_shib_redirect_url() """
#     #     updated_shib_status = 'will_force_logout'
#     #     app_login_url = '%s://%s%s?%s' % ( scheme, host, reverse('delivery:login_url'), session_dct['last_querystring'] )  # app_login_url isn't the shib url; it's the url to this login-app
#     #     log.debug( 'app_login_url, `%s`' % app_login_url )
#     #     encoded_app_login_url = urlquote( app_login_url )  # django's urlquote()
#     #     force_logout_redirect_url = '%s?return=%s' % ( settings_app.SHIB_LOGOUT_URL_ROOT, encoded_app_login_url )
#     #     redirect_tuple = ( force_logout_redirect_url, updated_shib_status )
#     #     log.debug( 'redirect_tuple, `{}`'.format(redirect_tuple) )
#     #     return redirect_tuple

#     # def _make_force_login_redirect_url( self, scheme, host, session_dct ):
#     #     """ Builds login-redirect url
#     #         Called by build_shib_redirect_url()
#     #         Note, fyi, normally a shib httpd.conf entry triggers login via a config line like `require valid-user`.
#     #             This SHIB_LOGIN_URL setting, though, is a url like: `https://host/shib.sso/login?target=/this_url_path`
#     #             ...so it's that shib.sso/login url that triggers the login, not this app login url.
#     #             This app login url _is_ shib-configured, though to perceive shib headers if they exist. """
#     #     updated_shib_status = 'will_force_login'
#     #     encoded_openurl = urlquote( session_dct.get('last_querystring', '') )
#     #     force_login_redirect_url = '%s?%s' % ( settings_app.SHIB_LOGIN_URL, encoded_openurl )
#     #     redirect_tuple = ( force_login_redirect_url, updated_shib_status )
#     #     log.debug( 'redirect_tuple, `{}`'.format(redirect_tuple) )
#     #     return redirect_tuple

#     def update_user( self, localdev, meta_dct, host ):
#         """ For now just returns shib_dct;
#             eventually with create or update a user object and return that.
#             Called by views.login() """
#         if localdev is False:
#             shib_dct = shib_checker.grab_shib_info( meta_dct, host )
#         else:  # localdev
#             shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
#         log.debug( 'shib_dct, `%s`' % pprint.pformat(shib_dct) )
#         return shib_dct

#     # end class LoginViewHelper()
