# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json,logging, pprint, re, urlparse
from datetime import datetime

import requests

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from py360link2 import get_sersol_data
from shorturls import baseconv

from findit import app_settings, forms, summon
from findit.utils import BulSerSol
from delivery.models import Resource


log = logging.getLogger('access')
# plink = Permalink()


class FinditResolver( object ):
    """ Handles views.findit_base_resolver() calls. """

    def __init__(self):
        self.enhanced_link = False
        self.sersol_publication_link = False
        self.borrow_link = False
        self.referrer = ''

    def check_index_page( self, querydict ):
        """ Checks to see if it's the demo landing page.
            Called by views.base_resolver() """
        log.debug( 'querydict, `%s`' % querydict )
        return_val = False
        if querydict == {} or ( querydict.keys() == ['output'] and querydict.get('output', '') == 'json' ):
            return_val = True
        log.debug( 'return_val, `%s`' % return_val )
        return return_val

    def make_index_context( self, querydict ):
        """ Builds context for index page.
            Called by views.base_resolver() """
        context = { 'SS_KEY': settings.BUL_LINK_SERSOL_KEY, 'easyWhat': 'easyAccess' }
        return context

    def make_index_response( self, request, context ):
        """ Returns json or html response object for index.html or resolve.html template.
            Called by views.base_resolver() """
        if request.GET.get('output', '') == 'json':
            output = json.dumps( context, sort_keys=True, indent = 2 )
            resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
        else:
            resp = render( request, 'findit/index.html', context )
        log.debug( 'returning response' )
        return resp

    def check_summon( self, querydict ):
        """ Determines whether a summon check is needed.
            Called by views.base_resolver() """
        referrer = self._get_referrer( querydict ).lower()
        check_summon = True
        for provider in settings.FINDIT_SKIP_SUMMON_DIRECT_LINK:
            if referrer.find( provider ) > 0:
                check_summon = False
                break
        log.debug( 'check_summon, `%s`' % check_summon )
        return check_summon

    def enhance_link( self, direct_indicator, query_string ):
        """ Enhances link via summon lookup if necessary.
            Called by views.base_resolver() """
        enhanced = False
        if direct_indicator is not 'false':  # "ensure the GET request doesn't override this" -- (bjd: don't fully understand this; i assume this val is set somewhere)
            enhanced_link = summon.get_enhanced_link( query_string )  # TODO - use the metadata from Summon to render the request page rather than hitting the 360Link API for something that is known not to be held.
            if enhanced_link:
                self.enhanced_link = enhanced_link
                enhanced = True
        log.debug( "enhanced, `%s`; enhanced_link, `%s`" % (enhanced, self.enhanced_link) )
        return enhanced

    def check_sersol_publication( self, rqst_qdict, rqst_qstring ):
        """ Handles journal requests; passes them on to 360link for now.
            Called by views.base_resolver() """
        sersol_journal = False
        if rqst_qdict.get('rft.genre', 'null') == 'journal' or rqst_qdict.get('genre', 'null') == 'journal':
            if rqst_qdict.get( 'sid', 'null' ).startswith( 'FirstSearch' ):
                issn = rqst_qdict.get( 'rft.issn' )  # TODO: remove this or return it if necessary
                self.sersol_publication_link = 'http://%s.search.serialssolutions.com/?%s' % ( settings.BUL_LINK_SERSOL_KEY, rqst_qstring)
                sersol_journal = True
        log.debug( "sersol_journal, `%s`; sersol_publication_link, `%s`" % (sersol_journal, self.sersol_publication_link) )
        return sersol_journal

    def check_book( self, rqst_qdict, rqst_qstring ):
        """ Handles book requests; builds /borrow redirect link.
            Called by views.base_resolver() """
        is_book = False
        if rqst_qdict.get('genre', 'null') == 'book' or rqst_qdict.get('rft.genre', 'null') == 'book':
            url = reverse( 'delivery:resolve' ) + '?%s' % rqst_qstring
            log.debug( 'book url, `%s`' % url )
            self.borrow_link = url
            is_book = True
        log.debug( 'is_book, `%s`' % is_book )
        return is_book

    def update_querystring( self, querystring  ):
        """ Updates querystring if necessary to catch non-standard pubmed queries.
            Called by views.base_resolver() """
        PMID_QUERY = re.compile('^pmid\:(\d+)')
        pmid_match = re.match( PMID_QUERY, querystring )
        if pmid_match:
            log.debug( 'non-standard pmid found' )
            pmid = pmid_match.group(1)
            updated_querystring = 'pmid=%s' % pmid
        else:
            log.debug( 'non-standard pmid not found' )
            updated_querystring = querystring
        return updated_querystring

    def get_sersol_dct( self, scheme, host, querystring ):
        """ Builds initial data-dict.
            Called by views.base_resolver() """
        sersol_dct = get_sersol_data( querystring, key='rl3tp7zf5x' )  # get_sersol_data() is a function of pylink3602
        log.debug( 'sersol_dct, ```%s```' % pprint.pformat(sersol_dct) )
        return sersol_dct

    def check_book_after_sersol( self, sersol_dct, rqst_qstring ):
        """ Handles book requests after sersol lookup; builds /borrow redirect link.
            Called by views.base_resolver() """
        is_book = False
        results = sersol_dct.get( 'results', '' )
        if type( results ) == list:
            if len( results ) > 0:
                if type( results[0] ) == dict:
                    if results[0].get( 'format', '' ) == 'book':
                        url = reverse( 'delivery:resolve' ) + '?%s' % rqst_qstring
                        self.borrow_link = url
                        is_book = True
        log.debug( 'is_book, `%s`; self.borrow_link, `%s`' % (is_book, self.borrow_link) )
        return is_book

    def make_resolve_context( self, permalink, qstring, sersol_dct ):
        """ Preps the template view.
            Called by views.base_resolver() """
        context = self._try_resolved_obj_citation( sersol_dct )
        context['easyWhat'] = self._check_genre( context )
        context['permalink'] = permalink
        context['SS_KEY'] = settings.BUL_LINK_SERSOL_KEY
        context['querystring'] = qstring
        log.debug( 'context, ```%s```' % pprint.pformat(context) )
        return context

    # def update_session( self, request, context ):
    #     """ Updates session for illiad-request-check if necessary.
    #         Called by views.base_resolver() """
    #     if context.get( 'resolved', False ) == False:
    #         request.session['findit_illiad_check_flag'] = 'good'
    #         openurl = request.META.get('QUERY_STRING', '')
    #         if openurl is not '':
    #             request.session['findit_illiad_check_openurl'] = request.META.get('QUERY_STRING', '')
    #         citation_json = json.dumps( context.get('citation', {}), sort_keys=True, indent=2 )
    #         request.session['citation'] = citation_json
    #         request.session['format'] = context.get( 'format', '' )
    #         initial_illiad_url = app_settings.ILLIAD_URL_ROOT % openurl  # root already has an '%s' in it
    #         request.session['illiad_url'] = '%s&sid=%s' % (initial_illiad_url, self.referrer)
    #     log.debug( 'request.session.__dict__ now, `%s`' % pprint.pformat(request.session.__dict__) )
    #     return

    # def update_session( self, request, context ):
    #     """ Updates session for illiad-request-check if necessary.
    #         Called by views.base_resolver() """
    #     if context.get( 'resolved', False ) == False:
    #         request.session['findit_illiad_check_flag'] = 'good'
    #         request.session['format'] = context.get( 'format', '' )
    #         openurl = request.META.get('QUERY_STRING', '')
    #         request.session['findit_illiad_check_openurl'] = openurl
    #         citation_json = json.dumps( context.get('citation', {}), sort_keys=True, indent=2 )
    #         request.session['citation'] = citation_json
    #         initial_illiad_url = app_settings.ILLIAD_URL_ROOT % openurl  # root already has an '%s' in it
    #         request.session['illiad_url'] = '%s&sid=%s' % (initial_illiad_url, self.referrer)
    #     log.debug( 'request.session.__dict__ now, `%s`' % pprint.pformat(request.session.__dict__) )
    #     return

    def update_session( self, request, context ):
        """ Updates session for illiad-request-check if necessary.
            Called by views.base_resolver() """
        if context.get( 'resolved', False ) == False:
            request.session['findit_illiad_check_flag'] = 'good'
            request.session['format'] = context.get( 'format', '' )
            openurl = request.META.get('QUERY_STRING', '')
            request.session['findit_illiad_check_openurl'] = openurl
            citation_json = json.dumps( context.get('citation', {}), sort_keys=True, indent=2 )
            request.session['citation'] = citation_json
            genre = self._make_genre( openurl, request.GET )
            request.session['illiad_url'] = self._make_illiad_url( openurl, context.get('format', ''), genre )
        log.debug( 'request.session.__dict__ now, `%s`' % pprint.pformat(request.session.__dict__) )
        return

    def make_resolve_response( self, request, context ):
        """ Returns json or html response object for index.html or resolve.html template.
            Called by views.base_resolver()
            TODO: refactor. """
        if request.GET.get('output', '') == 'json':
            output = json.dumps( context, sort_keys=True, indent = 2 )
            resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
        else:
            resp = render( request, 'findit/resolve.html', context )
        log.debug( 'returning response' )
        return resp

    ## helper defs

    def _get_referrer( self, querydict ):
        """ Gets the referring site to append to links headed elsewhere.
            Helpful for tracking down ILL request sources.
            Called by check_summon() """
        ( sid, ea ) = ( None, 'easyAccess' )
        sid = querydict.get( 'sid', None )
        if not sid:  # then try rfr_id
            sid = querydict.get( 'rfr_id', None )
        if sid:
            self.referrer = '%s-%s' % ( sid, ea )
        else:
            self.referrer = ea
        log.debug( 'self.referrer, `%s`' % self.referrer )
        return self.referrer

    def _try_resolved_obj_citation( self, sersol_dct ):
        """ Returns initial context based on a resolved-object.
            Called by make_resolve_context() """
        context = {}
        try:
            resolved_obj = BulSerSol( sersol_dct )
            log.debug( 'resolved_obj.__dict__, ```%s```' % pprint.pformat(resolved_obj.__dict__) )
            context = resolved_obj.access_points()
            ( context['citation'], context['link_groups'], context['format'] ) = ( resolved_obj.citation, resolved_obj.link_groups, resolved_obj.format )
        except Exception as e:
            log.error( 'exception resolving object, ```%s```' % unicode(repr(e)) )
            context['citation'] = {}
        log.debug( 'context after resolve, ```%s```' % pprint.pformat(context) )
        return context

    def _check_genre( self, context ):
        """ Sets `easyBorrow` or `easyArticle`.
            Called by make_resolve_context()"""
        (genre, genre_type) = ('', 'easyArticle')
        if 'citation' in context.keys() and 'genre' in context['citation'].keys():
            genre = context['citation']['genre']
        log.debug( 'genre, `%s`' % genre )
        if genre == 'book':
            genre_type = 'easyBorrow'
        log.debug( 'genre_type, `%s`' % genre_type )
        return genre_type

    def _make_genre( self, openurl, rqst_qdict ):
        """ Gets genre for illiad url.
            Called by update_session()
            TODO, think about how to combine with _check_genre() """
        if 'genre' not in openurl:
            genre = rqst_qdict.get('rft.genre', '')
            if genre == '':
                genre = rqst_qdict.get('genre', '')
            if genre == '':
                genre = 'article'
        return genre

    def _make_illiad_url( self, openurl, format, genre ):
        """ Builds illiad url for storage in session on failed resolve.
            Called by update_session() """
        openurl = '%s&genre=%s' % ( openurl, genre )
        if 'format' not in openurl:
            openurl = '%s&format=%s' % ( openurl, format )
        initial_illiad_url = app_settings.ILLIAD_URL_ROOT % openurl  # root already has an '%s' in it
        illiad_url = '%s&sid=%s' % ( initial_illiad_url, self.referrer )
        log.debug( 'illiad_url, ```%s```' % illiad_url )
        return illiad_url

    ## end class FinditResolver
