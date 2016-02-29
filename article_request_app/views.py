# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random, time
from .classes.illiad_helper import IlliadHelper
from .classes.login_helper import LoginHelper
from .classes.shib_helper import ShibChecker
from article_request_app import settings_app
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from illiad.account import IlliadSession


log = logging.getLogger( 'access' )
ilog = logging.getLogger( 'illiad' )
ill_helper = IlliadHelper()
login_helper = LoginHelper()
shib_checker = ShibChecker()


def login( request ):
    """ Ensures user comes from correct 'findit' url;
        then forces login;
        then checks illiad for new-user or blocked;
        if happy, redirects to `illiad`, otherwise to `oops`. """

    ## check that request is from findit
    if login_helper.check_referrer( request ) is False:
        return HttpResponseBadRequest( 'See "https://library.brown.edu/easyaccess/" for example easyAccess requests.`' )

    ## force login, by forcing a logout
    ( localdev, shib_status ) = login_helper.assess_status( request )
    if localdev is False:
        if shib_status == '':  # clean entry, force logout, sets shib_status to 'will_force_logout'
            return HttpResponseRedirect( login_helper.make_force_logout_redirect_url( request ) )
        elif shib_status == 'will_force_logout':  # sets shib_status to 'will_force_login'
            return HttpResponseRedirect( login_helper.make_force_login_redirect_url( request ) )
        elif shib_status == 'will_force_login' and request.META.get('Shibboleth-eppn', '') == '':  # handles occasional issue; normally shib headers are ok
            return HttpResponseRedirect( login_helper.make_force_logout_redirect_url( request ) )

    ## get user info
    shib_dct = login_helper.grab_user_info( request, localdev, shib_status )  # updates session with user info

    ## log user into illiad
    ( illiad_instance, success ) = ill_helper.login_user( request, shib_dct )
    if success is False:
        return HttpResponseRedirect( reverse('article_request:oops_url') )  # handles blocked or failed-user-registration problems

    ## illiad logout
    ill_helper.logout_user( illiad_instance )

    ## build redirect to illiad-landing-page for submit
    illiad_landing_redirect_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:illiad_request_url'), request.session['login_openurl'] )
    log.debug( 'illiad_landing_redirect_url, `%s`' % illiad_landing_redirect_url )

    ## cleanup
    login_helper.update_session( request )

    ## redirect
    return HttpResponseRedirect( illiad_landing_redirect_url )


def illiad_request( request ):
    """ Gives users chance to confirm their request via clicking 'Submit'."""
    ## check that we're here legitimately
    here_check = False
    illiad_login_check_flag = request.session.get( 'illiad_login_check_flag', '' )
    login_openurl = request.session.get( 'login_openurl', '' )
    request.session['login_openurl'] = ''
    log.debug( 'illiad_login_check_flag, `%s`' % illiad_login_check_flag )
    if illiad_login_check_flag == 'good' and login_openurl == request.META.get('QUERY_STRING', ''):
        here_check = True
    log.debug( 'here_check, `%s`' % here_check )
    if here_check is True:
        request.session['illiad_request_openurl'] = request.META.get('QUERY_STRING', '')
    else:
        log.warning( 'bad attempt from source-url, ```%s```; ip, `%s`' % (
            request.META.get('HTTP_REFERER', ''), request.META.get('REMOTE_ADDR', '') ) )
        return HttpResponseBadRequest( 'Bad request; see "https://library.brown.edu/easyaccess/" for example usage.`' )
    ## prep data
    citation_json = request.session.get( 'citation', '{}' )
    format = request.session.get( 'format', '' )
    context = { 'citation': json.loads(citation_json), 'format': format }
    ## cleanup
    request.session['citation'] = ''
    request.session['format'] = ''
    request.session['illiad_login_check_flag'] = ''
    ## respond
    resp = render( request, 'article_request_app/request.html', context )
    return resp


def illiad_handler( request ):
    """ Processes the confirmation 'Submit' button behind-the-scenes,
        then redirects the user to the confirmation-info page. """
    ## here check
    here_check = 'init'
    openurl = request.session.get( 'illiad_request_openurl', '' )
    if len( openurl ) == 0:
        here_check = 'problem'
    if here_check == 'init':
        shib_dct = json.loads( request.session.get('user', '{}') )
    if 'eppn' not in shib_dct.keys():
        here_check = 'problem'
    if here_check == 'problem':
        log.warning( 'bad attempt from source-url, ```%s```; ip, `%s`' % (
            request.META.get('HTTP_REFERER', ''), request.META.get('REMOTE_ADDR', '') ) )
        return HttpResponseBadRequest( 'Bad request' )

    ## get illiad_instance
    ill_username = shib_dct['eppn'].split('@')[0]
    log.debug( 'ill_username, `%s`' % ill_username )
    illiad_instance = IlliadSession( settings_app.ILLIAD_REMOTE_AUTH_URL, settings_app.ILLIAD_REMOTE_AUTH_HEADER, ill_username )
    log.debug( 'illiad_instance.__dict__, ```%s```' % pprint.pformat(illiad_instance.__dict__) )
    try:
        illiad_session = illiad_instance.login()
    except Exception as e:
        log.error( 'Exception on illiad login, ```%s```' % unicode(repr(e)) )
        message = 'oops; a problem occurred'
        request.session['problem_message'] = message
        return HttpResponseRedirect( reverse('article_request:oops_url') )

    ## submit to illiad
    illiad_url = request.session['illiad_url']
    illiad_post_key = illiad_instance.get_request_key( illiad_url )
    log.debug( 'illiad_post_key, ```%s```' % pprint.pformat(illiad_post_key) )
    errors = illiad_post_key.get( 'errors', None )
    if errors:
        log.warning( 'errors during illiad submission: username, `%s`; message, ```%s```' % (ill_username, illiad_post_key['message']) )
    else:
        submit_status = illiad_instance.make_request( illiad_post_key )
        log.debug( 'submit_status, ```%s```' % pprint.pformat(submit_status) )
        illiad_transaction_number = submit_status['transaction_number']

    ## illiad logout
    try:
        illiad_instance.logout()
        log.debug( 'illiad logout successful' )
    except Exception as e:
        log.debug( 'illiad logout exception, ```%s```' % unicode(repr(e)) )

    ## update db eventually

    ## redirect
    confirmation_redirect_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:confirmation_url'), openurl )
    log.debug( 'confirmation_redirect_url, `%s`' % confirmation_redirect_url )

    ## cleanup

    ## redirect
    return HttpResponseRedirect( confirmation_redirect_url )

    # end def illiad_handler()


def confirmation( request ):
    return HttpResponse( 'confirmation-coming' )


def logout( request ):
    return HttpResponse( 'logout-coming' )


def oops( request ):
    message = request.session.get( 'problem_message', 'sorry; a problem occurred' )
    request.session['problem_message'] = ''
    return HttpResponse( message )
