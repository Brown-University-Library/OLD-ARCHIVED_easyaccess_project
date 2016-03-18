# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random, time
import markdown
from .classes.illiad_helper import IlliadHelper
from .classes.login_helper import LoginHelper
# from .classes.shib_helper import ShibChecker
from article_request_app import settings_app
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from illiad.account import IlliadSession


log = logging.getLogger( 'access' )
ilog = logging.getLogger( 'illiad' )
ill_helper = IlliadHelper()
login_helper = LoginHelper()
# shib_checker = ShibChecker()


def login( request ):
    """ Ensures user comes from correct 'findit' url;
        then forces login;
        then checks illiad for new-user or blocked;
        if happy, redirects to `illiad`, otherwise to `oops`. """

    ## check that request is from findit
    referrer_check = login_helper.check_referrer( request.session, request.META )
    if referrer_check is False:
        return HttpResponseBadRequest( 'See "https://library.brown.edu/easyaccess/" for example easyAccess requests.`' )
    else:
        request.session['login_openurl'] = request.META.get('QUERY_STRING', '')

    ## force login, by forcing a logout if needed
    ( localdev_check, redirect_check, shib_status ) = login_helper.assess_shib_redirect_need( request.session, request.get_host(), request.META )
    if redirect_check is True:
        ( redirect_url, updated_shib_status ) = login_helper.build_shib_redirect_url( shib_status=shib_status, scheme='https', host=request.get_host(), session_dct=request.session, meta_dct=request.META )
        request.session['shib_status'] = updated_shib_status
        return HttpResponseRedirect( redirect_url )

    ## get user info
    shib_dct = login_helper.grab_user_info( request, localdev_check, shib_status )  # updates session with user info

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
        shib_dct = json.loads( request.session.get('user_json', '{}') )
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
        request.session['problem_message'] = 'There was a problem submitting your request; please try again later.'
        return HttpResponseRedirect( reverse('article_request:oops_url') )
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

    ## send email
    subject = 'easyAccess request confirmation'
    body = ill_helper.make_illiad_success_message(
        shib_dct['name_first'], shib_dct['name_last'], request.session.get('citation'), illiad_transaction_number, shib_dct['email'] )
    ffrom = settings_app.EMAIL_FROM
    addr = shib_dct['email']
    send_mail(
        subject, body, ffrom, [addr], fail_silently=True )

    ## prep redirect
    # request.session['message'] = body
    request.session['message'] = '{}\n---'.format( body )
    # message_redirect_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('article_request:message_url'), openurl )
    message_redirect_url = reverse('article_request:message_url')
    log.debug( 'message_redirect_url, `%s`' % message_redirect_url )

    ## cleanup
    request.session['citation'] = ''

    ## redirect
    return HttpResponseRedirect( message_redirect_url )

    # end def illiad_handler()


def message( request ):
    """ Handles successful confirmation messages and problem messages. """
    context = {
        'last_path': request.session.get( 'last_path', '' ),
        'message': markdown.markdown( request.session.get('message', '') )
        }
    request.session['last_path'] = request.path
    return render( request, 'article_request_app/message.html', context )
