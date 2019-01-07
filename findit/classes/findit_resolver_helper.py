# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint, random, re, time, urllib, urlparse
from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.text import slugify
from findit import app_settings, summon
from findit.classes.illiad_helper import IlliadUrlBuilder
from findit.utils import BulSerSol
from py360link2 import get_sersol_data
# from shorturls import baseconv


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
        self.log_id = ''
        # self.ABOUT_PATH = unicode( os.environ['EZACS__FINDIT_ABOUT_PATH'] )

    def get_log_id( self ):
        """ Returns log-identifier string.
            Called by views.findit_base_resolver() """
        self.log_id = '{}'.format( random.randint(10000, 99999) )
        return self.log_id

    def check_index_page( self, querydict ):
        """ Checks to see if it's the demo landing page.
            Called by views.findit_base_resolver() """
        log.debug( 'querydict, `%s`' % querydict )
        return_val = False
        if querydict == {} or ( querydict.keys() == ['output'] and querydict.get('output', '') == 'json' ):
            return_val = True
        # log.debug( 'return_val, `%s`' % return_val )
        log.debug( '`{id}` return_val, `{val}`'.format(id=self.log_id, val=return_val) )
        return return_val

    def make_index_context( self, querydict, scheme, host, permalink, ip ):
        """ Builds context for index page.
            Called by views.findit_base_resolver() """
        # full_permalink = '%s://%s%s' % ( request.scheme, request.get_host(), permalink )
        full_permalink = '%s://%s%s' % ( scheme, host, permalink )
        log.debug( 'full_permalink, ```%s```' % full_permalink )
        context = {
            'is_index_page': True,  # enables css to apply underline
            'SS_KEY': settings.BUL_LINK_SERSOL_KEY,
            'easyWhat': 'easyAccess',
            'feedback_link': app_settings.PROBLEM_URL % ( full_permalink, ip )  # settings contains string-substitution for permalink & ip
        }
        return context

    def make_index_response( self, request, context ):
        """ Returns json or html response object for index.html or resolve.html template.
            Called by views.findit_base_resolver() """
        if request.GET.get('output', '') == 'json':
            output = json.dumps( context, sort_keys=True, indent=2 )
            resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
        else:
            resp = render( request, 'findit/index.html', context )
        log.debug( '`{id}` returning index response'.format(id=self.log_id) )
        return resp

    def check_double_encoded_querystring( self, querystring ):
        """ Checks for apache redirect-bug.
            Called by views.findit_base_resolver() """
        return_val = False
        if '%25' in querystring:
            good_querystring = urllib.unquote( querystring )
            self.redirect_url = '{main_url}?{querystring}'.format( main_url=reverse('findit:findit_base_resolver_url'), querystring=good_querystring )
            return_val = True
        # log.debug( 'bad url found, {}'.format(return_val) )
        log.debug( '`{id}` bad url check, `{val}`'.format(id=self.log_id, val=return_val) )
        return return_val

    def check_summon( self, querydict ):
        """ Determines whether a summon check is needed.
            Called by views.findit_base_resolver() """
        referrer = self._get_referrer( querydict ).lower()
        log.debug( 'referrer, `%s`' % referrer )
        check_summon = True
        for provider in settings.FINDIT_SKIP_SUMMON_DIRECT_LINK:
            if referrer.find( provider ) > 0:
                log.debug( 'skipping summon for this referrer' )
                check_summon = False
                break
        # log.debug( 'check_summon, `%s`' % check_summon )
        log.debug( '`{id}` check_summon result, `{val}`'.format(id=self.log_id, val=check_summon) )
        return check_summon

    def enhance_link( self, direct_indicator, query_string ):
        """ Enhances link via summon lookup if necessary.
            Called by views.findit_base_resolver()
            Try/except handles a summon.py error ```return self.response['documents']``` with an associated response, excerpted...
            ```{u'errors': [{u'code': u'too.many.requests',
                          u'message': u'The system is currently experiencing a higher than normal traffic volume. Please retry this request at a later time.',``` """
        enhanced = False
        enhanced_link = None
        if direct_indicator is not 'false':  # "ensure the GET request doesn't override this" -- (bjd: don't fully understand this; i assume this val is set somewhere)
            try:
                enhanced_link = summon.get_enhanced_link( query_string )  # TODO - use the metadata from Summon to render the request page rather than hitting the 360Link API for something that is known not to be held.
            except Exception as e:
                log.debug( '`{id}` handled exception, ```{val}```'.format(id=self.log_id, val=unicode(repr(e))) )
                time.sleep(2)
                try:
                    enhanced_link = summon.get_enhanced_link( query_string )
                except Exception as e:
                    log.debug( '`{id}` 2nd handled exception, ```{val}```'.format(id=self.log_id, val=unicode(repr(e))) )
            if enhanced_link:
                self.enhanced_link = enhanced_link
                enhanced = True
        log.debug( '`{id}` enhanced-check result, `{bool}`; enhanced-link, ```{link}```'.format(id=self.log_id, bool=enhanced, link=self.enhanced_link) )
        return enhanced

    def check_sersol_publication( self, rqst_qdict, rqst_qstring ):
        """ Handles journal requests; passes them on to 360link for now.
            Called by views.findit_base_resolver() """
        sersol_journal = False
        if rqst_qdict.get('rft.genre', 'null') == 'journal' or rqst_qdict.get('genre', 'null') == 'journal':
            if rqst_qdict.get( 'sid', 'null' ).startswith( 'FirstSearch' ):
                # issn = rqst_qdict.get( 'rft.issn' )  # TODO: remove this or return it if necessary
                self.sersol_publication_link = 'http://%s.search.serialssolutions.com/?%s' % ( settings.BUL_LINK_SERSOL_KEY, rqst_qstring)
                sersol_journal = True
        # log.debug( "sersol_journal, `%s`; sersol_publication_link, `%s`" % (sersol_journal, self.sersol_publication_link) )
        log.debug( '`{id}` sersol_journal-check result, `{val}`'.format(id=self.log_id, val=sersol_journal) )
        return sersol_journal

    def check_ebook( self, sersol_dct ):
        """ Checks if item has an ebook, and if so, returns the label and url.
            Returns tuple: ( ebook_exists, label, url )
            Called by views.findit_base_resolver() """
        return_tuple = ( False, '', '' )
        if sersol_dct.get( 'results', None ):
            for result in sersol_dct['results']:
                if result.get( 'linkGroups', None ):
                    for link_group in result['linkGroups']:
                        return_tuple = self._check_group_for_ebook( link_group, return_tuple )
                        if return_tuple[0]:
                            break
                if return_tuple[0]:
                    break
        log.debug( '`{id}` ebook check complete'.format(id=self.log_id) )
        return return_tuple

    def _check_group_for_ebook( self, link_group, return_tuple ):
        """ Checks link_group for values indicating an ebook.
            Returns tuple: ( ebook_exists, label, url )
            Called by check_ebook() """
        ( holding_data_dct, lg_type, url_dct ) = ( link_group.get('holdingData', {}), link_group.get('type', ''), link_group.get('url', {}) )
        if holding_data_dct and lg_type == 'holding' and url_dct:
            ( database_name, journal_url ) = ( holding_data_dct.get('databaseName', ''), url_dct.get('journal', '') )
            if database_name and journal_url:
                return_tuple = ( True, database_name, journal_url )
        # log.debug( 'return_tuple, ```{}```'.format(pprint.pformat(return_tuple)) )
        log.debug( '`{id}` ebook check fields "boolean", "database_name", "journal_url", ```{val}```'.format(id=self.log_id, val=pprint.pformat(return_tuple)) )
        return return_tuple

    def check_book( self, request ):
        """ Checks if request is for a book.
            If so, builds /borrow redirect link and updates session.
            Called by views.findit_base_resolver() """
        ( is_book, querydct, querystring ) = ( False, request.GET, request.META.get('QUERY_STRING', '') )
        if querydct.get('genre', 'null') == 'book' or querydct.get('rft.genre', 'null') == 'book':
            is_book = True
            # self.borrow_link = reverse( 'delivery:resolve' ) + '?%s' % querystring  # keep for now
            self.borrow_link = reverse( 'delivery:availability_url' ) + '?%s' % querystring
            log.debug( 'self.borrow_link, `%s`' % self.borrow_link )
            # request.session['last_path'] = request.path
            request.session['last_path'] = reverse( 'findit:findit_base_resolver_url' )
            request.session['last_querystring'] = querystring
        # log.debug( 'is_book, `%s`' % is_book )
        log.debug( '`{id}` is_book, `{val}`'.format(id=self.log_id, val=is_book) )
        return is_book

    def update_querystring( self, querystring  ):
        """ Updates querystring if necessary to catch non-standard pubmed queries.
            Called by views.findit_base_resolver() """
        PMID_QUERY = re.compile('^pmid\:(\d+)')
        pmid_match = re.match( PMID_QUERY, querystring )
        if pmid_match:
            # log.debug( 'non-standard pmid found' )
            pmid = pmid_match.group(1)
            updated_querystring = 'pmid=%s' % pmid
            log.debug( '`{id}` non-standard pmid found, updated_querystring, ```{val}```'.format(id=self.log_id, val=updated_querystring) )
        else:
            # log.debug( 'non-standard pmid not found' )
            log.debug( '`{id}` no non-standard pmid found'.format(id=self.log_id) )
            updated_querystring = querystring
        return updated_querystring

    def get_sersol_dct( self, scheme, host, querystring ):
        """ Builds initial data-dict.
            Called by views.findit_base_resolver()
            Error note:
                Occational ```XMLSyntaxError(u'Opening and ending tag mismatch: hr line 1 and body, line 1, column 922',)``` caused by unknown blip.
                Result: eventual redirect to  citation form for confirmation -- always seems to work second time. """
        try:
            sersol_dct = get_sersol_data( querystring, key=app_settings.SERSOL_KEY )  # get_sersol_data() is a function of py360link2
        except Exception as e:
            log.debug( '`{id}` problem grabbing sersol data, ```{val}```'.format(id=self.log_id, val=unicode(repr(e))) )
            sersol_dct = {}
        log.debug( '`{id}` sersol_dct, ```{val}```'.format(id=self.log_id, val=pprint.pformat(sersol_dct)) )
        return sersol_dct

    def prep_eds_fulltext_url( self, querystring ):
        """ Checks querystring for submitted eds fulltext url.
            Updates it and returns it.
            Called by views.findit_base_resolver() """
        eds_fulltext_url = None
        parse_result = urlparse.parse_qs( querystring )
        log.debug( 'parse_result, ```%s```' % pprint.pformat(parse_result) )
        url_lst = parse_result.get( 'ebscoperma_link', None )  # single-element list
        if url_lst:
            probable_url = url_lst[0]
            parse2_result = urlparse.parse_qs( probable_url )
            log.debug( 'parse2_result, ```%s```' % pprint.pformat(parse2_result) )
            if 'AN' in parse2_result.keys() and 'db' in parse2_result.keys():
                eds_fulltext_url = 'https://login.revproxy.brown.edu/login?url=%s' % probable_url  # url-param intentionally not encoded for revproxy
        log.debug( 'eds_fulltext_url, ```%s```' % eds_fulltext_url )
        return eds_fulltext_url

    def add_eds_fulltext_url( self, eds_fulltext_url, sersol_dct ):
        """ Adds fulltext-url to sersol-dct.
            Called by views.findit_base_resolver() """
        if 'results' in sersol_dct.keys():
            if type( sersol_dct['results'] ) == list:
                for results_element in sersol_dct['results']:
                    # log.debug( 'results_element, ```%s```' % pprint.pformat(results_element) )
                    ( key, value_lst ) = results_element.items()[0]
                    if key == 'linkGroups':
                        if type( results_element['linkGroups'] ) == list:
                            new_holdings_dct = {
                                'holdingData': {
                                    'databaseId': '',
                                    'databaseName': 'EBSCO Discovery Service',
                                    'providerId': '',
                                    'providerName': 'EBSCO Discovery Service',
                                    'startDate': ''},
                                'type': 'holding',
                                'url': {
                                    'article': eds_fulltext_url,
                                    'issue': '',
                                    'journal': '',
                                    'source': ''}
                            }
                            results_element['linkGroups'].append(new_holdings_dct)
                            break
        log.debug( 'returning sersol_dct, ```%s```' % pprint.pformat(sersol_dct) )
        return sersol_dct

    def check_bad_issn( self, sersol_dct ):
        """ Checks for invalid issn and builds redirect url.
            Called by views.findit_base_resolver()
            Info: EDS sometimes puts bad metadata into the issn field.
                  The 360Link-api can detect this, so check for the condition and handle it. """
        ( is_bad_issn, redirect_url ) = ( False, None )
        if 'diagnostics'in sersol_dct.keys():
            for diagnostic_entry in sersol_dct['diagnostics']:
                if 'message' in diagnostic_entry.keys() and 'details' in diagnostic_entry.keys():
                    if 'Invalid check sum' == diagnostic_entry['message']:
                        if 'Removed issn:' in diagnostic_entry['details']:
                            if 'echoedQuery' in sersol_dct.keys():
                                if 'queryString' in sersol_dct['echoedQuery'].keys():
                                    is_bad_issn = True
                                    issnless_querystring = self.remove_issn_val( sersol_dct['echoedQuery']['queryString'] )
                                    redirect_url = '{main_url}?{querystring}'.format( main_url=reverse('findit:findit_base_resolver_url'), querystring=issnless_querystring )
                                    break
        return_val = ( is_bad_issn, redirect_url )
        log.debug( 'is_bad_issn, `%s`; redirect_url, ```%s```' % (is_bad_issn, redirect_url) )
        return return_val

    def remove_issn_val( self, bad_querystring ):
        """ Removes bad issn val from querystring.
            Called by check_bad_issn() """
        pieces = bad_querystring.split( '&' )
        indices = [i for i, piece in enumerate(pieces) if 'issn=' in piece]  # generally, like, `[5]`
        for element in indices:
            pieces[element] = 'issn='
        better_querystring = '&'.join( pieces )
        log.debug( 'better_querystring, ```%s```' % better_querystring )
        return better_querystring

    def check_pubmed_result( self, sersol_dct ):
        """ Checks sersol_dct for occasional situation in which a pubmed result for a journal has a format of 'book'.
            Called by views.findit_base_resolver() """
        try:
            citation = sersol_dct['results'][0]['citation']
            format = sersol_dct['results'][0]['format']
            if format == 'book':
                if 'pmid' in citation.keys() and 'volume' in citation.keys():
                    sersol_dct['results'][0]['format'] = 'journal'
                    log.debug( 'sersol_dct updated, now, ```{}```'.format(pprint.pformat(sersol_dct)) )
        except Exception as e:
            log.debug( 'ok error on pubmed book check, ```{}```'.format(unicode(repr(e))) )
            sersol_dct = sersol_dct
        log.debug( 'sersol_dct not updated' )
        return sersol_dct

    def check_bad_data( self, querystring, sersol_dct ):
        """ Checks sersol_dct response for indicator of bad or incomplete data.
            Returns redirect_url to citation form, and problem-message, if data's not good.
            Called by views.findit_base_resolver() """
        ( data_bad, redirect_url, problem_message ) = ( True, 'init', 'init' )
        try:
            if sersol_dct['diagnostics'][0]['message'] == 'Not enough metadata supplied':
                log.info( '`{id}` detected not-enough-metadata'.format(id=self.log_id) )
                problem_message = 'There was not enough information provided to complete your request. Please add more information about the resource. A Journal, ISSN, DOI, or PMID is required.'
            elif sersol_dct['diagnostics'][0]['message'] == 'Invalid syntax':
                log.info( '`{id}` detected bad-metadata'.format(id=self.log_id) )
                problem_message = 'Please add-to or confirm the information about this resource. A Journal, ISSN, DOI, or PMID is required.'
            redirect_url = '{citation_url}?{openurl}'.format( citation_url=reverse('findit:citation_form_url'), openurl=querystring )
        except Exception:  # a good exception! no diagnostics message means data is good
            log.info( '`{id}` detected good-metadata'.format(id=self.log_id) )
            ( data_bad, redirect_url, problem_message ) = ( False, None, None )
        return ( data_bad, redirect_url, problem_message )

    def check_direct_link( self, sersol_dct ):
        """ Checks for a direct link, and if so, returns True and updates self.direct_link with the url.
            Called by views.findit_base_resolver() """
        return_val = False
        if sersol_dct.get( 'results', None ):
            for result in sersol_dct['results']:
                if result.get( 'linkGroups', None ):
                    for group in result['linkGroups']:
                        return_val = self._check_group_for_direct_link( group )
                        if return_val:
                            break
                if return_val:
                    break
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
            Called by views.findit_base_resolver() """
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

    def make_resolve_context( self, request, permalink, querystring, sersol_dct ):
        """ Preps the template view.
            Called by views.findit_base_resolver() """
        context = self._try_resolved_obj_citation( sersol_dct )
        context = self.check_citation_issn( context )
        ( context['genre'], context['easyWhat'] ) = self._check_genre( context )
        if context.get( 'enhanced_querystring', '' ) == '':
            context['enhanced_querystring'] = querystring
        context['querystring'] = querystring
        context['ris_url'] = '{ris_url}?{eq}'.format( ris_url=reverse('findit:ris_url'), eq=context['enhanced_querystring'] )
        context['permalink'] = permalink
        context['SS_KEY'] = settings.BUL_LINK_SERSOL_KEY
        ip = request.META.get( 'REMOTE_ADDR', 'unknown' )
        full_permalink = '%s://%s%s' % ( request.scheme, request.get_host(), permalink )
        context['feedback_link'] = app_settings.PROBLEM_URL % ( full_permalink, ip )  # settings contains string-substitution for permalink & ip
        log.debug( 'context, ```%s```' % pprint.pformat(context) )
        return context

    def update_session( self, request, context ):
        """ Updates session for illiad-request-check if necessary.
            Called by views.findit_base_resolver() """
        if context.get( 'resolved', False ) is False:
            request.session['findit_illiad_check_flag'] = 'good'
            request.session['format'] = context.get( 'format', '' )
            request.session['findit_illiad_check_enhanced_querystring'] = context['enhanced_querystring']
            citation_json = json.dumps( context.get('citation', {}), sort_keys=True, indent=2 )
            request.session['citation_json'] = citation_json
            request.session['illiad_url'] = ill_url_builder.make_illiad_url( context['enhanced_querystring'], context['permalink'] )
            request.session['last_path'] = request.path
        log.debug( 'request.session.items(), `%s`' % pprint.pformat(request.session.items()) )
        return

    def make_resolve_response( self, request, context ):
        """ Returns json or html response object for index.html or resolve.html template.
            Called by views.base_resolver()
            TODO: refactor. """
        if request.GET.get('output', '') == 'json':
            output = json.dumps( context, sort_keys=True, indent=2 )
            resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
        else:
            # resp = render( request, 'findit/resolve.html', context )
            resp = render( request, 'findit/resolve_josiah.html', context )
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
            Called by make_resolve_context()
            Exeption note:
                Occasional ```Link360Exception(u'Invalid syntax Invalid check sum',)``` caused by data being sent like: `rft.jtitle={content.jtitle}`.
                Result: eventual redirect to  citation form for confirmation -- always seems to work second time. """
        log.debug( '`{id}` sersol_dct start, ```{val}```'.format(id=self.log_id, val=pprint.pformat(sersol_dct)) )  # does not show the openurl
        context = {}
        try:
            resolved_obj = BulSerSol( sersol_dct )
            log.debug( '`{id}` resolved_obj.__dict__, ```{val}```'.format(id=self.log_id, val=pprint.pformat(resolved_obj.__dict__)) )  # does not show the openurl
            log.debug( '`{id}` resolved_obj.openurl, ```{val}```'.format(id=self.log_id, val=resolved_obj.openurl) )
            context = resolved_obj.access_points()
            ( context['citation'], context['link_groups'], context['format'] ) = ( resolved_obj.citation, resolved_obj.link_groups, resolved_obj.format )
            context['enhanced_querystring'] = resolved_obj.openurl
        except Exception as e:
            log.error( 'exception resolving object, ```%s```' % unicode(repr(e)) )
            context['citation'] = {}
        log.debug( 'context after resolve, ```%s```' % pprint.pformat(context) )
        return context

    def check_citation_issn( self, context ):
        """ Creates `citation_display` for template use.
            Called by: make_resolve_context() """
        citation = context.get( 'citation', None )
        if citation:
            try:
                issn = citation.get('issn', {}).values()[0]
            except ( IndexError, AttributeError ):
                issn = citation.get('issn', '')
            citation['issn_display'] = issn
        log.debug( 'context after citation update, ```%s```' % citation )
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

    ## end class FinditResolver
