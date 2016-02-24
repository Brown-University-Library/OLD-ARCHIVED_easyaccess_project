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
from illiad.account import IlliadSession


log = logging.getLogger( 'access' )
ilog = logging.getLogger( 'illiad' )
# validator = Validator()
# view_helper = ViewHelper()


def login( request ):
    """ Ensures user comes from correct 'findit' url;
        then forces login; then checks illiad for new-user or blocked;
        if happy, redirects to `illiad`, otherwise to `oops`. """

    ## check that request is from findit
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


    # ## force login, by forcing a logout if necessary
    # login_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:login_url'), request.session['login_openurl'] )  # for logout and login redirections
    # log.debug( 'login_url, `%s`' % login_url )
    # localdev = False
    # shib_status = request.session.get('shib_status', '')
    # log.debug( 'shib_status, `%s`' % shib_status )
    # if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
    #     localdev = True
    # if not localdev and shib_status == '':  # we need to force logout
    #     request.session['shib_status'] = 'will_force_logout'
    #     encoded_login_url = urlquote( login_url )  # django's urlquote()
    #     force_logout_redirect_url = '%s?return=%s' % ( settings_app.SHIB_LOGOUT_URL_ROOT, encoded_login_url )
    #     log.debug( 'force_logout_redirect_url, `%s`' % force_logout_redirect_url )
    #     return HttpResponseRedirect( force_logout_redirect_url )
    # if not localdev and shib_status == 'will_force_logout':  # force login
    #     request.session['shib_status'] = 'will_force_login'
    #     # force_login_redirect_url = '%s' % settings_app.SHIB_LOGIN_URL
    #     encoded_openurl = urlquote( request.session['login_openurl'] )
    #     force_login_redirect_url = '%s?%s' % ( settings_app.SHIB_LOGIN_URL, encoded_openurl )
    #     log.debug( 'force_login_redirect_url, `%s`' % force_login_redirect_url )
    #     return HttpResponseRedirect( force_login_redirect_url )

    ## force login, by forcing a logout if necessary
    login_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:login_url'), request.session['login_openurl'] )  # for logout and login redirections
    log.debug( 'login_url, `%s`' % login_url )
    localdev = False
    shib_status = request.session.get('shib_status', '')
    # log.debug( 'shib_status, `%s`' % shib_status )
    if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
        localdev = True
    if not localdev and shib_status == '':  # force login
        request.session['shib_status'] = 'will_force_login'
        encoded_openurl = urlquote( request.session['login_openurl'] )
        force_login_redirect_url = '%s?%s' % ( settings_app.SHIB_LOGIN_URL, encoded_openurl )
        log.debug( 'force_login_redirect_url, `%s`' % force_login_redirect_url )
        return HttpResponseRedirect( force_login_redirect_url )


    ## get user info
    if not localdev and shib_status == 'will_force_login':
        eppn = request.META.get( 'Shibboleth-eppn', 'anonymous' )
    else:  # localdev
        shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        eppn = shib_dct['eppn']

    ## log user into illiad
    ilog.debug( 'about to initialize an illiad session' )
    # illiad = IlliadSession(
    #     ILLIAD_REMOTE_AUTH_URL,
    #     ILLIAD_REMOTE_AUTH_HEADER,
    #     ill_username )
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
