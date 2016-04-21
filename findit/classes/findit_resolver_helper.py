# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint, re, urllib, urlparse
from datetime import datetime

import bibjsontools, requests
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.text import slugify
from findit import app_settings, forms, summon
from findit.classes.illiad_helper import IlliadUrlBuilder
from findit.utils import BulSerSol
from py360link2 import get_sersol_data
from shorturls import baseconv


log = logging.getLogger('access')
ill_url_builder = IlliadUrlBuilder()


class RisHelper( object ):
    """ Assists download of RIS file like:
        TY  - BOOK
        PY  - 2005
        PB  - Scholastic Press
        AU  - Muth, Jon
        SN  - 9780439339117
        TI  - Zen shorts
        [RIS]( https://en.wikipedia.org/wiki/RIS_(file_format) ) """

    def make_title( self, bib_dct ):
        """ Grabs title from bib_dct else uses datestamp.
            Called by views.ris_citation() """
        title = bib_dct.get( 'title', unicode(datetime.now()).replace(' ', '_') )
        slugified_title = slugify( title )
        log.debug( 'slugified_title, `{}`'.format(slugified_title) )
        return slugified_title

    # end class RisHelper


class FinditResolver( object ):
    """ Handles views.findit_base_resolver() calls. """

    def __init__(self):
        self.enhanced_link = False
        self.sersol_publication_link = False
        self.borrow_link = False
        self.direct_link = False
        self.referrer = ''
        self.redirect_url = ''

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

    def check_double_encoded_querystring( self, querystring ):
        """ Checks for apache redirect-bug.
            Called by views.base_resolver() """
        return_val = False
        if '%25' in querystring:
            good_querystring = urllib.unquote( querystring )
            self.redirect_url = '{main_url}?{querystring}'.format( main_url=reverse('findit:findit_base_resolver_url'), querystring=good_querystring )
            return_val = True
        log.debug( 'bad url found, {}'.format(return_val) )
        return return_val

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

    def check_ebook( self, sersol_dct ):
        """ Checks if item has an ebook, and if so, returns the label and url.
            Returns tuple: ( ebook_exists, label, url )
            Called by views.base_resolver() """
        return_tuple = ( False, '', '' )
        if sersol_dct.get( 'results', None ):
            for result in sersol_dct['results']:
                if result.get( 'linkGroups', None ):
                    for link_group in result['linkGroups']:
                        return_tuple = self._check_group_for_ebook( link_group, return_tuple )
                        if return_tuple[0]: break
                if return_tuple[0]: break
        log.debug( 'return_tuple, ```{}```'.format(pprint.pformat(return_tuple)) )
        return return_tuple

    def _check_group_for_ebook( self, link_group, return_tuple ):
        """ Checks link_group for values indicating an ebook.
            Returns tuple: ( ebook_exists, label, url )
            Called by check_ebook() """
        ( holding_data_dct, lg_type, url_dct ) = ( link_group.get('holdingData', {}), link_group.get('type', ''), link_group.get('url', {}) )
        if holding_data_dct and lg_type=='holding' and url_dct:
            ( database_name, journal_url ) = ( holding_data_dct.get('databaseName', ''), url_dct.get('journal', '') )
            if database_name and journal_url:
                return_tuple = ( True, database_name, journal_url )
        log.debug( 'return_tuple, ```{}```'.format(pprint.pformat(return_tuple)) )
        return return_tuple

    def check_book( self, request ):
        """ Checks if request is for a book.
            If so, builds /borrow redirect link and updates session.
            Called by views.base_resolver() """
        ( is_book, querydct, querystring ) = ( False, request.GET, request.META.get('QUERY_STRING', '') )
        if querydct.get('genre', 'null') == 'book' or querydct.get('rft.genre', 'null') == 'book':
            is_book = True
            # self.borrow_link = reverse( 'delivery:resolve' ) + '?%s' % querystring  # keep for now
            self.borrow_link = reverse( 'delivery:availability_url' ) + '?%s' % querystring
            log.debug( 'self.borrow_link, `%s`' % self.borrow_link )
            request.session['last_path'] = request.path
            request.session['last_querystring'] = querystring
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
        try:
            sersol_dct = get_sersol_data( querystring, key=app_settings.SERSOL_KEY )  # get_sersol_data() is a function of pylink3602
        except Exception as e:
            log.error( 'exception grabbing sersol data, ```{}```'.format(unicode(repr(e))) )
            sersol_dct = {}
        log.debug( 'sersol_dct, ```%s```' % pprint.pformat(sersol_dct) )
        return sersol_dct

    def check_direct_link( self, sersol_dct ):
        """ Checks for a direct link, and if so, returns True and updates self.direct_link with the url.
            Called by views.base_resolver() """
        return_val = False
        if sersol_dct.get( 'results', None ):
            for result in sersol_dct['results']:
                if result.get( 'linkGroups', None ):
                    for group in result['linkGroups']:
                        return_val = self._check_group_for_direct_link( group )
                        if return_val: break
                if return_val: break
        log.debug( 'return_val, `{}`'.format(return_val) )
        return return_val

    def _check_group_for_direct_link( self, group ):
        """ Checks a linkGroup's data for an article url; if found, updates self.direct_link
            Called by check_direct_link() """
        return_val = False
        if group.get( 'type', '' ) == 'holding':
            if group.get( 'url', None ):
                if group['url'].get( 'article', None ):
                    self.direct_link = group['url']['article']
                    return_val = True
        log.debug( 'return_val, `{}`'.format(return_val) )
        return return_val

    def check_book_after_sersol( self, sersol_dct, rqst_qstring ):
        """ Handles book requests after sersol lookup; builds /borrow redirect link.
            Called by views.base_resolver() """
        is_book = False
        results = sersol_dct.get( 'results', '' )
        if type( results ) == list:
            if len( results ) > 0:
                if type( results[0] ) == dict:
                    if results[0].get( 'format', '' ) == 'book':
                        url = reverse( 'delivery:availability_url' ) + '?%s' % rqst_qstring
                        self.borrow_link = url
                        is_book = True
        log.debug( 'is_book, `%s`; self.borrow_link, `%s`' % (is_book, self.borrow_link) )
        return is_book

    # def make_resolve_context( self, request, permalink, querystring, sersol_dct ):
    #     """ Preps the template view.
    #         Called by views.base_resolver() """
    #     context = self._try_resolved_obj_citation( sersol_dct )
    #     ( context['genre'], context['easyWhat'] ) = self._check_genre( context )
    #     context['querystring'] = querystring
    #     context['enhanced_querystring'] = self._enhance_querystring( querystring, context['citation'], context['genre'] )
    #     context['permalink'] = permalink
    #     context['SS_KEY'] = settings.BUL_LINK_SERSOL_KEY
    #     ip = request.META.get( 'REMOTE_ADDR', 'unknown' )
    #     context['problem_link'] = app_settings.PROBLEM_URL % ( permalink, ip )  # settings contains string-substitution for permalink & ip
    #     log.debug( 'context, ```%s```' % pprint.pformat(context) )
    #     return context

    def make_resolve_context( self, request, permalink, querystring, sersol_dct ):
        """ Preps the template view.
            Called by views.base_resolver() """
        context = self._try_resolved_obj_citation( sersol_dct )
        ( context['genre'], context['easyWhat'] ) = self._check_genre( context )
        enhanced_querystring = self._enhance_querystring( querystring, context['citation'], context['genre'] )
        ( context['querystring'], context['enhanced_querystring'] ) = ( querystring, enhanced_querystring )
        context['ris_url'] = '{ris_url}?{eq}'.format( ris_url=reverse('findit:ris_url'), eq=enhanced_querystring )
        context['permalink'] = permalink
        context['SS_KEY'] = settings.BUL_LINK_SERSOL_KEY
        ip = request.META.get( 'REMOTE_ADDR', 'unknown' )
        context['problem_link'] = app_settings.PROBLEM_URL % ( permalink, ip )  # settings contains string-substitution for permalink & ip
        log.debug( 'context, ```%s```' % pprint.pformat(context) )
        return context

    def update_session( self, request, context ):
        """ Updates session for illiad-request-check if necessary.
            Called by views.base_resolver() """
        if context.get( 'resolved', False ) == False:
            request.session['findit_illiad_check_flag'] = 'good'
            request.session['format'] = context.get( 'format', '' )
            request.session['findit_illiad_check_enhanced_querystring'] = context['enhanced_querystring']
            citation_json = json.dumps( context.get('citation', {}), sort_keys=True, indent=2 )
            request.session['citation'] = citation_json
            request.session['illiad_url'] = ill_url_builder.make_illiad_url( context['enhanced_querystring'] )
            request.session['last_path'] = request.path
        log.debug( 'request.session.items(), `%s`' % pprint.pformat(request.session.items()) )
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
        """ Sets `easyBorrow` or `easyArticle`, and context genre.
            Called by make_resolve_context()"""
        ( genre, genre_type ) = ( 'article', 'easyArticle' )
        if 'citation' in context.keys():
            if 'genre' in context['citation'].keys():
                genre = context['citation']['genre']
        if genre == 'book':
            genre_type = 'easyBorrow'
        log.debug( 'genre, `%s`; genre_type, `%s`' % (genre, genre_type) )
        return ( genre, genre_type )

    def _enhance_querystring( self, querystring, citation_dct, genre ):
        """ Takes original querystring openurl and adds to it from citation info.
            Called by make_resolve_context() """
        citation_dct['type'] = genre
        initial_citation_querystring = bibjsontools.to_openurl( citation_dct )
        updated_citation_dct = bibjsontools.from_openurl( initial_citation_querystring )
        bib_dct = bibjsontools.from_openurl( querystring )
        for (key, val) in bib_dct.items():
            if key not in updated_citation_dct.keys():
                updated_citation_dct[key] = val
        enhanced_querystring = urllib.unquote( bibjsontools.to_openurl(updated_citation_dct) )
        log.debug( 'enhanced_querystring, ```%s```' % enhanced_querystring )
        return enhanced_querystring

    ## end class FinditResolver
