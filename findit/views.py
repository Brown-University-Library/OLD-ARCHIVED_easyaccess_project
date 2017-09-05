# -*- coding: utf-8 -*-

from __future__ import unicode_literals
"""
Views for the resolver.
"""

## stdlib
import datetime, json, logging, pprint, re, urllib2

## other
import bibjsontools

from . import app_settings, forms, summon
from .app_settings import BOOK_RESOLVER, ILLIAD_REMOTE_AUTH_URL, ILLIAD_REMOTE_AUTH_HEADER, EMAIL_FROM, MAS_KEY, PROBLEM_URL, SUMMON_ID, SUMMON_KEY,SERVICE_ACTIVE, EXTRAS_TIMEOUT, SERVICE_OFFLINE
from .classes.baseconv import base62
from .classes.citation_form_helper import CitationFormHelper
from .classes.findit_resolver_helper import FinditResolver
from .classes.findit_resolver_helper import RisHelper
from .classes.permalink_helper import Permalink
from .models import Request, UserMessage
from .utils import BulSerSol, Ourl
from .utils import get_cache_key, make_illiad_url
from bibjsontools import ris as bibjsontools_ris
from bul_link.views import BulLinkBase
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse, get_script_prefix
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render, render_to_response
from django.utils.decorators import method_decorator
from py360link2 import get_sersol_data, Link360Exception, Resolved


EXTRAS_CACHE_TIMEOUT = 604800 # 60*60*24*7 == one week
PMID_QUERY = re.compile('^pmid\:(\d+)')  # check for non-standard pubmed queries.

form_helper = CitationFormHelper()
permalink_helper = Permalink()
ris_helper = RisHelper()

ilog = logging.getLogger('illiad')
alog = logging.getLogger('access')


def citation_form( request ):
    """ Displays citation form on GET; redirects built url to /find/?... on POST. """
    ( form_helper.log_id, citation_form_message ) = ( request.session.get('log_id', ''), request.session.get('citation_form_message', '') )
    alog.debug( '`{id}` len-get-keys, `{len}`; request.GET, ```{get}```'.format(id=form_helper.log_id, len=len(request.GET.keys()), get=pprint.pformat(request.GET)) )
    if citation_form_message:
        request.session['citation_form_message'] = ''
    if len( request.GET.keys() ) == 0:
        context = form_helper.build_simple_context( request )
        alog.info( '`{id}` simple context built'.format(id=form_helper.log_id) )
    else:
        context = form_helper.build_context_from_url( request )
        alog.info( '`{id}` context built from querystring'.format(id=form_helper.log_id) )
    context['citation_form_message'] = citation_form_message
    response = form_helper.build_get_response( request, context )
    return response


def findit_base_resolver( request ):
    """ Handles link resolution. """

    fresolver = FinditResolver()
    log_id = fresolver.get_log_id()
    alog.info( '\n===\n`{}` starting...\n==='.format(log_id) )
    alog.info( '`{id}` request.__dict__, ```{dct}```'.format( id=log_id, dct=pprint.pformat(request.__dict__)) )

    ## start fresh
    alog.debug( 'session.items() before refresh, ```{}```'.format(pprint.pformat(request.session.items())) )
    for key in request.session.keys():
        del request.session[key]
    alog.debug( 'session.items() after refresh, ```{}```'.format(pprint.pformat(request.session.items())) )
    alog.info( '`{}` session cleared'.format(log_id) )
    request.session['log_id'] = log_id

    ## if index-page call
    if fresolver.check_index_page( request.GET ):
        context = fresolver.make_index_context( request.GET )
        resp = fresolver.make_index_response( request, context )
        alog.info( '`{}`returning index page'.format(log_id) )
        return resp

    ## temp fix for testing from in-production redirects
    if fresolver.check_double_encoded_querystring( unicode(request.META.get('QUERY_STRING', '')) ):
        alog.info( '`{id}` double-encoded querystring found, gonna redirect to, ```{url}```'.format(id=log_id, url=fresolver.redirect_url) )
        return HttpResponseRedirect( fresolver.redirect_url )

    ## make permalink if one doesn't exist
    querystring = request.META.get('QUERY_STRING', '')
    permalink_url = permalink_helper.make_permalink(
        referrer=request.GET.get('rfr_id',''), qstring=querystring, scheme=request.scheme, host=request.get_host(), path=reverse('findit:findit_base_resolver_url')
        )['permalink']
    request.session['permalink_url'] = permalink_url
    alog.info( '`{id}` permalink made, ```{url}```'.format(id=log_id, url=permalink_url) )

    # ## if summon returns an enhanced link, go to it
    # if fresolver.check_summon( request.GET ):
    #     if fresolver.enhance_link( request.GET.get('direct', None), querystring ):
    #         alog.info( '`{id}` redirecting to summon enhanced link, ```{link}```'.format(id=log_id, link=fresolver.enhanced_link) )
    #         return HttpResponseRedirect( fresolver.enhanced_link )

    ## if journal, redirect to 360link for now
    if fresolver.check_sersol_publication( request.GET, querystring ):
        alog.info( '`{id}` redirecting to sersol publication link, ```{link}```'.format(id=log_id, link=fresolver.sersol_publication_link) )
        return HttpResponseRedirect( fresolver.sersol_publication_link )

    ## get serials-solution data-dct
    querystring = fresolver.update_querystring( querystring )  # update querystring if necessary to catch non-standard pubmed ids
    sersol_dct = fresolver.get_sersol_dct( request.scheme, request.get_host(), querystring )
    alog.info( '`{}` sersol data-dct prepared'.format(log_id) )

    ## if available, add eds fulltext link to serials-solution data-dct
    eds_fulltext_url = fresolver.prep_eds_fulltext_url( querystring )
    if eds_fulltext_url:
        sersol_dct = fresolver.add_eds_fulltext_url( eds_fulltext_url, sersol_dct )

    ## if bad issn, remove it and redirect
    ( is_bad_issn, redirect_url ) = fresolver.check_bad_issn( sersol_dct )
    if is_bad_issn:
        alog.info( '`{id}` redirecting to non-issn url, ```{url}```'.format(id=log_id, url=redirect_url) )
        return HttpResponseRedirect( redirect_url )

    ## check for pubmed journal that says it's a book
    sersol_dct = fresolver.check_pubmed_result( sersol_dct )
    alog.info( '`{}` check for bad pubmed data complete'.format(log_id) )

    ## if not enough data, redirect to citation-form
    ( is_bad_data, redirect_url, problem_message ) = fresolver.check_bad_data( querystring, sersol_dct )
    if is_bad_data:
        request.session['citation_form_message'] = problem_message
        alog.info( '`{id}` problem-data; redirecting to citation-form, ```{url}```'.format(id=log_id, url=redirect_url) )
        return HttpResponseRedirect( redirect_url )

    ## if there's a direct-link, go right to it
    direct_link_check = fresolver.check_direct_link(sersol_dct)
    if direct_link_check is True and app_settings.FLY_TO_FULLTEXT is True:
        alog.info( '`{id}` redirecting to sersol direct-link, ```{url}```'.format(id=log_id, url=fresolver.direct_link) )
        return HttpResponseRedirect( fresolver.direct_link )
    else:
        alog.info( '`{id}` would have redirected to sersol direct-link, ```{url}``` if FLY_TO_FULLTEXT was True'.format(id=log_id, url=fresolver.direct_link) )

    ## if there's an ebook, put it in the session
    ( ebook_exists, ebook_label, ebook_url ) = fresolver.check_ebook( sersol_dct )
    alog.info( '`{}` ebook check complete'.format(log_id) )
    if ebook_exists is True:
        ebook_dct = { 'ebook_label': ebook_label, 'ebook_url':ebook_url }
        request.session['ebook_json'] = json.dumps( ebook_dct )

    ## if book, redirect to /borrow
    if fresolver.check_book( request ):
        alog.info( '`{id}` book, redirecting to, ```{url}```'.format(id=log_id, url=fresolver.borrow_link) )
        return HttpResponseRedirect( fresolver.borrow_link )

    ## if sersol-data shows it's a book, redirect to /borrow
    if fresolver.check_book_after_sersol( sersol_dct, querystring ):
        request.session['last_path'] = request.path
        request.session['last_querystring'] = querystring
        alog.info( '`{id}` book found on second-check, redirecting to, ```{url}```'.format(id=log_id, url=fresolver.borrow_link) )
        return HttpResponseRedirect( fresolver.borrow_link )

    ## build response context
    context = fresolver.make_resolve_context( request, permalink_url, querystring, sersol_dct )
    alog.info( '`{}` context built'.format(log_id) )

    ## check for problem
    """ Saw this when findit_resolver_helper._try_resolved_obj_citation() had the exception:
          `Link360Exception(u'Invalid syntax Invalid check sum',)` -- eventually handle elsewhere, but here for now. """
    if context['citation'].keys() == [ 'type' ]:
        redirect_url = '{citation_url}?{openurl}'.format( citation_url=reverse('findit:citation_form_url'), openurl=querystring )
        request.session['citation_form_message'] = 'Please confirm or enhance your request and click "Submit". A Journal, ISSN, DOI, or PMID is required.'
        alog.info( '`{id}` weirdness detected; redirecting to citation-form, ```{url}```'.format(id=log_id, url=redirect_url) )
        return HttpResponseRedirect( redirect_url )

    ## update session if necessary
    fresolver.update_session( request, context )
    alog.info( '`{}` session updated'.format(log_id) )

    ## return resolve response
    resp = fresolver.make_resolve_response( request, context )
    alog.info( '`{}` returning response'.format(log_id) )
    return resp

    ## end def findit_base_resolver()


def link360( request ):
    """ Returns 360link json response.
        Called by OCRA service. """
    fresolver = FinditResolver()
    log_id = fresolver.get_log_id()
    alog.info( '`{id}` OCRA request.__dict__, ```{dct}```'.format( id=log_id, dct=pprint.pformat(request.__dict__)) )
    querystring = request.META.get('QUERY_STRING', None)
    sersol_dct = fresolver.get_sersol_dct( request.scheme, request.get_host(), querystring )
    jsn = json.dumps( sersol_dct, sort_keys=True, indent=2 )
    return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )


def permalink( request, permalink_str ):
    """ Handles expansion and redirection back to '/find/?...' """
    openurl = permalink_helper.get_openurl( permalink_str )
    if openurl:
        redirect_url = '%s://%s%s?%s' % ( request.scheme, request.get_host(), reverse('findit:findit_base_resolver_url'), openurl )
        return HttpResponsePermanentRedirect( redirect_url )
    else:
        return HttpResponse( "<p>Sorry, couldn't find a full url for that permalink.<p>" )


def ris_citation( request ):
    """ Downloads a ris citation for endnote.
        [RIS]( https://en.wikipedia.org/wiki/RIS_(file_format) )
        Triggered via click of `Export to Endnote` link on book page. """
    querystring = request.META.get('QUERY_STRING', None)
    if not querystring:
        return HttpResponseBadRequest( 'Sorry, no data found to parse for EndNote.' )
    bib_dct = bibjsontools.from_openurl( querystring )
    slugified_title = ris_helper.make_title( bib_dct )
    ris_string = bibjsontools_ris.convert( bib_dct )
    response = HttpResponse( ris_string, content_type='application/x-research-info-systems' )
    response['Content-Disposition'] = 'attachment; filename={}.ris'.format( slugified_title )
    return response


def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context: None
    """
    from django.shortcuts import render_to_response
    from django.template import RequestContext
    template_name = 'findit/500.html'
    resp = render_to_response(
        template_name,
        context_instance = RequestContext(request)
        )
    resp.status_code = 500
    return resp


def shib_info( request ):
    """ Displays user's shib_info. """
    try:
        shib_dct = { 'datetime': unicode(datetime.datetime.now()), 'ip_perceived': unicode(request.META.get('REMOTE_ADDR', 'unknown')) }
        for key in request.META.keys():
            if 'Shibboleth-' in key:
                if key in [ 'Shibboleth-eduPersonAffiliation', 'Shibboleth-eduPersonEntitlement', 'Shibboleth-eduPersonScopedAffiliation', 'Shibboleth-isMemberOf' ]:
                    elements = request.META[key].split( ';' )
                    shib_dct[key] = sorted( elements )
                else:
                    shib_dct[key] = request.META[key]
        jsn = json.dumps( shib_dct, sort_keys=True, indent=2 )
    except Exception as e:
        alog.debug( 'exception, `{}`'.format(unicode(repr(e))) )
        jsn = 'problem; unable to show your shib info'
    return HttpResponse( jsn, content_type='application/javascript; charset=utf-8' )
