# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from article_request_app import settings_app
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
# from .models import Validator, ViewHelper
from django.shortcuts import get_object_or_404, render
from django.utils.http import urlquote

log = logging.getLogger('access')
# validator = Validator()
# view_helper = ViewHelper()


# def check_login( request ):
#     """ Ensures user comes from correct 'findit' url, and that user is logged out of shib; then redirects to `login` """
#     log.debug( 'starting' )
#     ## findit check
#     findit_check = False
#     findit_illiad_check_flag = request.session.get( 'findit_illiad_check_flag', '' )
#     findit_illiad_check_openurl = request.session.get( 'findit_illiad_check_openurl', '' )
#     if findit_illiad_check_flag == 'good' and findit_illiad_check_openurl == request.META.get('QUERY_STRING', ''):
#         findit_check = True
#     log.debug( 'findit_check, `%s`' % findit_check )
#     if findit_check is True:
#         request.session['findit_illiad_check_flag'] = ''
#         request.session['findit_illiad_check_openurl'] = ''
#         request.session['check_login_flag'] = 'good'
#         request.session['check_login_openurl'] = request.META.get('QUERY_STRING', '')
#     elif findit_check is not True:
#         log.warning( 'Bad attempt from source-url, ```%s```; ip, `%s`' % (
#             request.META.get('HTTP_REFERER', ''), request.META.get('REMOTE_ADDR', '') ) )
#         message = 'To request an article, first'
#         return HttpResponseBadRequest( 'See "https://library.brown.edu/easyaccess/" for example usage.`' )

#     ## shib check to see if we need to force logout
#     log.debug( 'starting shib check' )

#     # redirect_url = '%s://%s%s' % ( request.scheme, request.get_host(), reverse('article_request:login_url') )  # the url shib-logout will redirect to
#     redirect_url = '%s://%s%s' % ( request.scheme, request.get_host(), reverse('article_request:confirmation_url') )  # the url shib-logout will redirect to

#     qstring = request.META.get('QUERY_STRING', '')
#     if qstring is not '':
#         redirect_url = '%s?%s' % ( redirect_url, qstring )
#     log.debug( 'request.META, ```%s```' % pprint.pformat(request.META) )
#     eppn = request.META.get( 'Shibboleth-eppn', '' )
#     log.debug( 'eppn, `%s`' % eppn )
#     if '@brown.edu' in eppn:
#         # logout( request )  # from django.contrib.auth import logout  # no, we don't want to destroy the session
#         if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
#             pass
#         else:
#             encoded_redirect_url = urlquote( redirect_url )  # django's urlquote()
#             redirect_url = '%s?return=%s' % ( os.environ['EZACS__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
#     log.debug( 'final redirect_url, `%s`' % redirect_url )
#     return HttpResponseRedirect( redirect_url )


# def login( request ):
#     check_login_flag = request.session.get( 'check_login_flag', '' )
#     check_login_openurl = request.session.get( 'check_login_openurl', '' )
#     login_forced = request.session.get( 'login_forced', '' )
#     if check_login_flag == 'good' and check_login_openurl == request.META.get('QUERY_STRING', '') and login_forced == '':
#         request.session['check_login_flag'] = ''
#         request.session['check_login_openurl'] = ''
#         request.session['login_forced'] = 'in_process'
#         request.session['login_openurl'] = request.META.get('QUERY_STRING', '')
#         redirect_url = settings_app.SHIB_LOGIN_URL
#         return HttpResponseRedirect( redirect_url )
#     elif login_forced == 'in_process':
#         ## do work
#         request.session['login_forced'] = ''
#         eppn = request.META.get( 'Shibboleth-eppn', 'anonymous' )
#         return HttpResponse( 'hi %s' % eppn )
#     else:
#         return HttpResponse( 'login-under-construction' )


def login( request ):
    ## check that we've come from findit
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
        return HttpResponseBadRequest( 'See "https://library.brown.edu/easyaccess/" for example usage.`' )

    ## see if we need to force logout
    login_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:login_url'), request.session['login_openurl'] )  # for logout and login redirections
    log.debug( 'login_url, `%s`' % login_url )
    localdev = False
    shib_status = request.session.get('shib_status', '')
    if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
        localdev = True
    if not localdev and shib_status == '':  # we need to force logout
        request.session['shib_status'] = 'will_force_logout'
        encoded_login_url = urlquote( login_url )  # django's urlquote()
        force_logout_redirect_url = '%s?return=%s' % ( settings_app.SHIB_LOGOUT_URL_ROOT, encoded_login_url )
        log.debug( 'force_logout_redirect_url, `%s`' % force_logout_redirect_url )
        return HttpResponseRedirect( force_logout_redirect_url )
    if not localdev and shib_status == 'will_force_logout':  # force login
        request.session['shib_status'] = 'will_force_login'
        force_login_redirect_url = '%s' % settings_app.SHIB_LOGIN_URL
        log.debug( 'force_login_redirect_url, `%s`' % force_login_redirect_url )
        return HttpResponseRedirect( force_login_redirect_url )

    ## get user info
    if not localdev and shib_status == 'will_force_login':
        eppn = request.META.get( 'Shibboleth-eppn', 'anonymous' )
    else:  # localdev
        shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        eppn = shib_dct['eppn']

    ## log user into illiad
    pass

    ## build redirect to illiad-landing-page for submit (if happy) or oops (on problem)
    illiad_landing_redirect_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:illiad_request_url'), request.session['login_openurl'] )
    log.debug( 'illiad_landing_redirect_url, `%s`' % illiad_landing_redirect_url )

    ## cleanup
    request.session['findit_illiad_check_flag'] = ''
    request.session['findit_illiad_check_openurl'] = ''
    request.session['login_openurl'] = ''
    request.session['shib_status'] = ''

    ## redirect
    return HttpResponseRedirect( illiad_landing_redirect_url )


def illiad_request( request ):
    context = {}
    resp = render( request, 'article_request_app/request.html', context )
    return resp


def confirmation( request ):
    return HttpResponse( 'confirmation-coming' )


def logout( request ):
    return HttpResponse( 'logout-coming' )


def oops( request ):
    return HttpResponse( 'oops-coming' )
