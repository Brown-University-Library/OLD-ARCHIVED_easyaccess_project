# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random, time
import markdown
from .classes.illiad_helper import IlliadHelper
from .classes.login_helper import LoginHelper
from article_request_app import settings_app
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.utils.http import urlquote
from illiad.account import IlliadSession


log = logging.getLogger( 'access' )
ilog = logging.getLogger( 'illiad' )
ill_helper = IlliadHelper()
login_helper = LoginHelper()


# def shib_login( request ):
#     """ Redirects to an SP login, which then lands back at the login_handler() url.
#         Called when views.availability() returns a Request button that's clicked. """
#     localdev_check = False
#     if request.get_host() == '127.0.0.1' and project_settings.DEBUG2 == True:  # eases local development
#         localdev_check = True
#     if localdev_check is True:
#         return HttpResponseRedirect( reverse('article_request:login_handler_url') )
#     login_handler_url = 'https://{host}{login_handler_url}'.format( host=request.get_host(), login_handler_url=reverse('article_request:login_handler_url') )
#     encoded_login_handler_url = urlquote( login_handler_url )
#     redirect_url = '{shib_login}?target={encoded_login_handler_url}'.format(
#         shib_login=settings_app.SHIB_LOGIN_URL, encoded_login_handler_url=encoded_login_handler_url )
#     log.debug( 'redirect_url, ```{}```'.format(redirect_url) )
#     return HttpResponseRedirect( redirect_url )


def shib_login( request ):
    """ Builds the SP login and target-return url; redirects to the SP login, which then lands back at the login_handler() url.
        Called when views.availability() returns a Request button that's clicked.
        Session cleared and info put in url due to revproxy resetting session. """
    log.debug( 'article_request shib_login() starting session.items(), ```{}```'.format(pprint.pformat(request.session.items())) )

    ## store vars we're gonna need
    citation_json = request.session.get( 'citation', '{}' )
    format = request.session.get( 'format', '' )
    illiad_url = request.session.get( 'illiad_url', '' )
    querystring = request.META.get('QUERY_STRING', '').decode('utf-8')

    ## clear session so non-rev and rev work same way
    for key in request.session.keys():
        del request.session[key]

    ## build login-handler url, whether it's direct (localdev), or indircect-via-shib
    login_handler_querystring = 'citation_json={ctn_jsn}&format={fmt}&illiad_url={ill_url}&querystring={qs}'.format(
        ctn_jsn=urlquote(citation_json), fmt=urlquote(format), ill_url=urlquote(illiad_url), qs=urlquote(querystring)
        )
    login_handler_url = '{scheme}://{host}{login_handler_url}?{querystring}'.format(
        scheme=request.scheme, host=request.get_host(), login_handler_url=reverse('article_request:login_handler_url'), querystring=login_handler_querystring )
    log.debug( 'pre-encoded login_handler_url, ```{}```'.format(login_handler_url) )

    ## return response
    localdev_check = False
    if request.get_host() == '127.0.0.1' and project_settings.DEBUG2 == True:  # eases local development
        localdev_check = True
    if localdev_check is True:
        log.debug( 'localdev_check is True, redirecting right to pre-encoded login_handler' )
        return HttpResponseRedirect( login_handler_url )
    else:
        encoded_login_handler_url = urlquote( login_handler_url )
        redirect_url = '{shib_login}?target={encoded_login_handler_url}'.format(
            shib_login=app_settings.SHIB_LOGIN_URL, encoded_login_handler_url=encoded_login_handler_url )
        log.debug( 'redirect_url to shib-sp-login, ```{}```'.format(redirect_url) )
        return HttpResponseRedirect( redirect_url )


def login_handler( request ):
    """ Ensures user comes from correct 'findit' url;
        then grabs shib info;
        then checks illiad for new-user or blocked;
        if happy, redirects to `illiad`, otherwise to `message` with error info. """

    ## check referrer
    # ( referrer_ok, redirect_url ) = login_helper.check_referrer( request.session, request.META )
    # if referrer_ok is not True:
    #     request.session['last_path'] = request.path
    #     return HttpResponseRedirect( redirect_url )
    log.debug( 'request.GET.keys(), ```{}```'.format(pprint.pformat(request.GET.keys())) )
    for key in [ 'citation_json', 'format', 'illiad_url', 'querystring' ]:

        if key not in request.GET.keys():
            redirect_url = '{main}?{qs}'.format( main=reverse('findit:findit_base_resolver_url'), qs=request.META.get('QUERY_STRING', '') )
            log.debug( 'referrer-check failed, redirecting to, ```{}```'.format(redirect_url) )
            return HttpResponseRedirect( redirect_url )
    request.session['last_path'] = request.path
    # request.session['login_openurl'] = request.META.get('QUERY_STRING', '')

    ## rebuild session (revproxy can destroy it, so all info must be in querystring)
    request.session['citation_json'] = request.GET['citation_json']
    request.session['format'] = request.GET['format']
    request.session['illiad_url'] = request.GET['illiad_url']
    request.session['login_openurl'] = request.GET['querystring']
    log.debug( 'session.items() after rebuild, ```{}```'.format(pprint.pformat(request.session.items())) )

    ## get user info
    # shib_dct = login_helper.grab_user_info( request, localdev_check, shib_status )  # updates session with user info
    localdev_check = False
    if request.get_host() == '127.0.0.1' and project_settings.DEBUG2 == True:  # eases local development
        localdev_check = True
    shib_dct = login_helper.grab_user_info( request, localdev_check )  # updates session with user info

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
    ( referrer_ok, redirect_url ) = ill_helper.check_referrer( request.session, request.META )
    if referrer_ok is not True:
        request.session['last_path'] = request.path
        return HttpResponseRedirect( redirect_url )
    request.session['last_path'] = request.path
    request.session['illiad_request_openurl'] = request.META.get('QUERY_STRING', '')

    ## prep data
    citation_json = request.session.get( 'citation', '{}' )
    format = request.session.get( 'format', '' )
    context = { 'citation': json.loads(citation_json), 'format': format }
    log.debug( 'context, ```{}```'.format(pprint.pformat(context)) )

    ## cleanup
    request.session['format'] = ''
    request.session['illiad_login_check_flag'] = ''
    log.debug( 'request.session.items(), ```{}```'.format(pprint.pformat(request.session.items())) )

    ## respond
    resp = render( request, 'article_request_app/request.html', context )
    return resp


def illiad_handler( request ):
    """ Processes the confirmation 'Submit' button behind-the-scenes,
        then redirects the user to the confirmation-info page. """

    # ## here check
    # here_check = 'init'
    # openurl = request.session.get( 'illiad_request_openurl', '' )
    # if len( openurl ) == 0:
    #     here_check = 'problem'
    # if here_check == 'init':
    #     shib_dct = json.loads( request.session.get('user_json', '{}') )
    # if 'eppn' not in shib_dct.keys():
    #     here_check = 'problem'
    # if here_check == 'problem':
    #     log.warning( 'bad attempt from source-url, ```%s```; ip, `%s`' % (
    #         request.META.get('HTTP_REFERER', ''), request.META.get('REMOTE_ADDR', '') ) )
    #     return HttpResponseBadRequest( 'Bad request' )

    ## here check
    here_check = 'init'
    illiad_url = request.session.get( 'illiad_url', '' )
    log.debug( 'illiad_url, ``{}```'.format(illiad_url) )
    if len( illiad_url ) == 0:
        here_check = 'problem'
    if here_check == 'init':
        shib_dct = json.loads( request.session.get('user_json', '{}') )
    if 'eppn' not in shib_dct.keys():
        here_check = 'problem'
    if here_check == 'problem':
        log.warning( 'bad attempt from source-url, ```%s```; ip, `%s`' % (
            request.META.get('HTTP_REFERER', ''), request.META.get('REMOTE_ADDR', '') ) )
        request.session['message'] = ill_helper.problem_message
        request.session['last_path'] = request.path
        return HttpResponseRedirect( reverse('article_request:message_url') )

    ## get illiad_instance
    ill_username = shib_dct['eppn'].split('@')[0]
    log.debug( 'ill_username, `%s`' % ill_username )
    illiad_instance = IlliadSession( settings_app.ILLIAD_REMOTE_AUTH_URL, settings_app.ILLIAD_REMOTE_AUTH_HEADER, ill_username )
    log.debug( 'illiad_instance.__dict__, ```%s```' % pprint.pformat(illiad_instance.__dict__) )
    try:
        illiad_session = illiad_instance.login()
    except Exception as e:
        log.error( 'Exception on illiad login, ```%s```' % unicode(repr(e)) )
        if request.session.get( 'message', '' ) == '':
            request.session['message'] = ill_helper.problem_message
        request.session['last_path'] = request.path
        return HttpResponseRedirect( reverse('article_request:message_url') )

    ## submit to illiad
    illiad_url = request.session['illiad_url']
    illiad_post_key = illiad_instance.get_request_key( illiad_url )
    log.debug( 'illiad_post_key, ```%s```' % pprint.pformat(illiad_post_key) )
    errors = illiad_post_key.get( 'errors', None )
    if errors:
        log.warning( 'errors during illiad submission: username, `%s`; message, ```%s```' % (ill_username, illiad_post_key['message']) )
        if request.session.get( 'message', '' ) == '':
            request.session['message'] = ill_helper.problem_message
        request.session['last_path'] = request.path
        return HttpResponseRedirect( reverse('article_request:message_url') )
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
        shib_dct['name_first'], shib_dct['name_last'], request.session.get('citation_json'), illiad_transaction_number, shib_dct['email'] )
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
    request.session['message'] = ''
    request.session['last_path'] = request.path
    return render( request, 'article_request_app/message.html', context )
