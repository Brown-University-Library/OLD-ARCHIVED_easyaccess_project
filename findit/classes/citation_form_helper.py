# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json,logging, pprint, re, urlparse
from datetime import datetime

import bibjsontools
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
# from django.utils.log import dictConfig
from findit import forms

# import requests
# from . import forms, summon
# from .app_settings import DB_SORT_BY, DB_PUSH_TOP, DB_PUSH_BOTTOM
# from .app_settings import PRINT_PROVIDER
# from .models import PrintTitle
# from django.core.urlresolvers import reverse
# from py360link2 import get_sersol_data, Resolved


# CURRENT_YEAR = datetime.now().year


# dictConfig( settings.LOGGING )
log = logging.getLogger('access')


class CitationFormDctMaker( object ):
    """ Converts django querystring-object to form-dct. """

    def make_form_dct( self, querydct ):
        """ Transfers metadata from openurl to dct for citation-linker form.
            Called by build_context_from_url(). """
        log.debug( 'querydct, ```%s```' % pprint.pformat(querydct) )
        qstring = ''
        for k,v in querydct.items():
            qstring = qstring + '%s=%s&' % (k,v)
        qstring = qstring[0:-1]
        log.debug( 'qstring, `%s`' % qstring )
        log.debug( 'type(qstring), `%s`' % type(qstring) )
        bibjson_dct = bibjsontools.from_openurl( qstring )
        log.debug( 'bibjson_dct, ```%s```' % pprint.pformat(bibjson_dct) )
        citation_form_dct = {}
        for k,v in querydct.items():
            # log.debug( 'querydict (k,v), `(%s,%s)`' % (k,v) )
            v = self._handle_v_list( v )
            ( k,v ) = self._handle_k( k,v )
            citation_form_dct[k] = v
        log.debug( 'initial_citation_form_dct, ```%s```' % pprint.pformat(citation_form_dct) )

        genre = self._check_genre( querydct )
        if genre == 'book':
            log.debug( 'in book handler')
            # fields unique to book-form: btitle, isbn, pub, place, spage, epage
            if citation_form_dct.get('btitle', None) == None:
                citation_form_dct['btitle'] = citation_form_dct.get('title', None)
            if citation_form_dct.get('pub', None) == None:
                citation_form_dct['pub'] = citation_form_dct.get('rft.pub', None)
            if citation_form_dct.get('place', None) == None:
                citation_form_dct['place'] = citation_form_dct.get('rft.place', None)

        else:  # article
            # fields unique to article-form: atitle, jtitle, issn, pmid, volume, issue
            if citation_form_dct.get('atitle', '').strip() == '':
                citation_form_dct['atitle'] = bibjson_dct.get( 'title', '' )
            if citation_form_dct.get('jtitle', '').strip() == '':
                if bibjson_dct.get( 'journal', '' ) is not '':
                    if bibjson_dct['journal'].get( 'name', '' ) is not '':
                        citation_form_dct['jtitle'] = bibjson_dct['journal']['name']
            if citation_form_dct.get('issn', '').strip() == '':
                if bibjson_dct.get( 'identifier', '' ) is not '':
                    for entry in bibjson_dct['identifier']:
                        if entry.get( 'type', '' ) == 'issn':
                            citation_form_dct['issn'] = entry['id']
                            break
            if citation_form_dct.get('pmid', '').strip() == '':
                pass  # TODO: implement
            if citation_form_dct.get('volume', '').strip() == '':
                citation_form_dct['volume'] = bibjson_dct.get( 'volume', '' )
            if citation_form_dct.get('issue', '').strip() == '':
                citation_form_dct['issue'] = bibjson_dct.get( 'issue', '' )

        # fields in both forma: 'au', 'date', 'id', 'pages', 'rfe_dat'
        if citation_form_dct.get('au', '').strip() == '':
            if bibjson_dct.get( 'author', '' ) is not '':
                authors = []
                for entry in bibjson_dct['author']:
                    if entry.get( 'name', '' ) is not '':
                        authors.append( entry['name'] )
                        citation_form_dct['au'] = ', '.join( authors )
                        break
        if citation_form_dct.get( 'date', '' ).strip() is '':
            if bibjson_dct.get( 'year', '' ) is not '':
                citation_form_dct['date'] = bibjson_dct['year']
        if citation_form_dct.get( 'id', '' ).strip() is '':
                if bibjson_dct.get( 'identifier', '' ) is not '':
                    for entry in bibjson_dct['identifier']:
                        if entry.get( 'type', '' ) == 'doi':
                            citation_form_dct['issn'] = entry['id']
                            break
        if citation_form_dct.get( 'pages', '' ).strip() is '':
            if bibjson_dct.get( 'pages', '' ) is not '':
                citation_form_dct['pages'] = bibjson_dct['pages'].replace( ' ', '' )
        else:
            citation_form_dct['pages'] = citation_form_dct['pages'].replace( ' ', '' )
        # TODO: try rfe_dat (oclcnum)
        log.debug( 'final citation_form_dct, ```%s```' % pprint.pformat(citation_form_dct) )
        return citation_form_dct

    def _check_genre( self, querydct ):
        """ Tries to determine genre. """
        genre = 'article'
        if querydct.get('genre') == 'book' or querydct.get('rft.genre') == 'book':
            genre = 'book'
        elif len(querydct.get('isbn', '')) > 0 or len(querydct.get('rft:isbn', '')) > 0:
            genre = 'book'
        log.debug( 'genre, `%s`' % genre )
        return genre

    def _handle_v_list(self, v):
        """ Handles querydict list values, and checks for a replace.
            Called by make_form_dct(). """
        # log.debug( 'initial v, `%s`' % v )
        if (v) and (v != '') and (type(v)==list):
            v = v[0]
        if type(v) == unicode and 'accessionnumber' in v:
            v = v.replace('<accessionnumber>', '').replace('</accessionnumber>', '')  # for oclc numbers
        log.debug( 'returned v, `%s`' % v )
        return v

    def _handle_k( self, k, v ):
        """ Handles two key situations.
            Called by make_form_dct(). """
        if k == 'id':
            if v.startswith('doi'):
                ( k,v ) = ( 'id', v.replace('doi:', '') )
        elif k == 'doi':
            k = 'id'
        log.debug( '(k,v), `(%s,%s)`' % (k,v) )
        return ( k,v )

    # end class CitationFormDictMaker


class CitationFormHelper( object ):
    """ Handles views.citation_form() calls. """

    def build_simple_context( self, request ):
        """ Prepares simple GET context.
            Called by views.citation_form() """
        context = {
            u'article_form': forms.ArticleForm,
            u'book_form': forms.BookForm,
            u'form_type': u'article',
            u'problem_link': u'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://127.0.0.1/citation-form/&entry_4=127.0.0.1',
            }
        log.debug( 'context, `%s`' % context )
        return context

    def build_context_from_url( self, request ):
        """ Populates form from url.
            Called by views.citation_form() """
        log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
        form_dct_maker = CitationFormDctMaker()
        citation_form_dct = form_dct_maker.make_form_dct( request.GET )
        context = {
            u'article_form': forms.ArticleForm(citation_form_dct),
            u'book_form': forms.BookForm(citation_form_dct),
            u'form_type': self.make_form_type( citation_form_dct ),
            u'problem_link': 'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://127.0.0.1/citation-form/&entry_4=127.0.0.1',
            }
        log.debug( 'context, `%s`' % context )
        return context

    def build_get_response( self, request, context ):
        """ Prepares GET response
            Called by views.citation_form() """
        resp = render( request, 'findit/citation_linker_2.html', context )
        log.debug( 'returning response' )
        return resp

    def make_form_type( self, dct ):
        """ Tries to get the default form right.
            Called by build_context_from_url() """
        form_type = 'article'
        if dct.get('isbn', '') is not '' and dct.get('issn', '') is '':
            form_type = 'book'
        elif dct.get('genre', '') == 'book':
            form_type = 'book'
        log.debug( 'form_type, `%s`' % form_type )
        return form_type

    # end class CitationFormHelper


# class CitationFormHelper( object ):
#     """ Handles views.citation_form() calls. """

#     def build_simple_context( self, request ):
#         """ Prepares simple GET context.
#             Called by views.citation_form() """
#         context = {
#             u'article_form': forms.ArticleForm,
#             u'book_form': forms.BookForm,
#             u'form_type': u'article',
#             u'problem_link': u'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://127.0.0.1/citation-form/&entry_4=127.0.0.1',
#             }
#         log.debug( 'context, `%s`' % context )
#         return context

#     def build_context_from_url( self, request ):
#         """ Populates form from url.
#             Called by views.citation_form() """
#         log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
#         citation_form_dct = self.make_form_dct( request.GET )
#         context = {
#             u'article_form': forms.ArticleForm(citation_form_dct),
#             u'book_form': forms.BookForm(citation_form_dct),
#             u'form_type': self.make_form_type( citation_form_dct ),
#             u'problem_link': 'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://127.0.0.1/citation-form/&entry_4=127.0.0.1',
#             }
#         log.debug( 'context, `%s`' % context )
#         return context

#     def build_get_response( self, request, context ):
#         """ Prepares GET response
#             Called by views.citation_form() """
#         resp = render( request, 'findit/citation_linker_2.html', context )
#         log.debug( 'returning response' )
#         return resp

#     ## helpers

#     def make_form_type( self, dct ):
#         """ Tries to get the default form right.
#             Called by build_context_from_url() """
#         form_type = 'article'
#         if dct.get('isbn', '') is not '' and dct.get('issn', '') is '':
#             form_type = 'book'
#         elif dct.get('genre', '') == 'book':
#             form_type = 'book'
#         log.debug( 'form_type, `%s`' % form_type )
#         return form_type

#     ## form prep for openurl ##

#     def make_form_dct( self, querydct ):
#         """ Transfers metadata from openurl to dct for citation-linker form.
#             Called by build_context_from_url(). """
#         log.debug( 'querydct, ```%s```' % pprint.pformat(querydct) )
#         qstring = ''
#         for k,v in querydct.items():
#             qstring = qstring + '%s=%s&' % (k,v)
#         qstring = qstring[0:-1]
#         log.debug( 'qstring, `%s`' % qstring )
#         log.debug( 'type(qstring), `%s`' % type(qstring) )
#         bibjson_dct = bibjsontools.from_openurl( qstring )
#         log.debug( 'bibjson_dct, ```%s```' % pprint.pformat(bibjson_dct) )
#         citation_form_dct = {}
#         for k,v in querydct.items():
#             # log.debug( 'querydict (k,v), `(%s,%s)`' % (k,v) )
#             v = self._handle_v_list( v )
#             ( k,v ) = self._handle_k( k,v )
#             citation_form_dct[k] = v
#         log.debug( 'initial_citation_form_dct, ```%s```' % pprint.pformat(citation_form_dct) )

#         genre = self._check_genre( querydct )
#         if genre == 'book':
#             log.debug( 'in book handler')
#             # fields unique to book-form: btitle, isbn, pub, place, spage, epage
#             if citation_form_dct.get('btitle', None) == None:
#                 citation_form_dct['btitle'] = citation_form_dct.get('title', None)
#             if citation_form_dct.get('pub', None) == None:
#                 citation_form_dct['pub'] = citation_form_dct.get('rft.pub', None)
#             if citation_form_dct.get('place', None) == None:
#                 citation_form_dct['place'] = citation_form_dct.get('rft.place', None)

#         else:  # article
#             # fields unique to article-form: atitle, jtitle, issn, pmid, volume, issue
#             if citation_form_dct.get('atitle', '').strip() == '':
#                 citation_form_dct['atitle'] = bibjson_dct.get( 'title', '' )
#             if citation_form_dct.get('jtitle', '').strip() == '':
#                 if bibjson_dct.get( 'journal', '' ) is not '':
#                     if bibjson_dct['journal'].get( 'name', '' ) is not '':
#                         citation_form_dct['jtitle'] = bibjson_dct['journal']['name']
#             if citation_form_dct.get('issn', '').strip() == '':
#                 if bibjson_dct.get( 'identifier', '' ) is not '':
#                     for entry in bibjson_dct['identifier']:
#                         if entry.get( 'type', '' ) == 'issn':
#                             citation_form_dct['issn'] = entry['id']
#                             break
#             if citation_form_dct.get('pmid', '').strip() == '':
#                 pass  # TODO: implement
#             if citation_form_dct.get('volume', '').strip() == '':
#                 citation_form_dct['volume'] = bibjson_dct.get( 'volume', '' )
#             if citation_form_dct.get('issue', '').strip() == '':
#                 citation_form_dct['issue'] = bibjson_dct.get( 'issue', '' )

#         # fields in both forma: 'au', 'date', 'id', 'pages', 'rfe_dat'
#         if citation_form_dct.get('au', '').strip() == '':
#             if bibjson_dct.get( 'author', '' ) is not '':
#                 authors = []
#                 for entry in bibjson_dct['author']:
#                     if entry.get( 'name', '' ) is not '':
#                         authors.append( entry['name'] )
#                         citation_form_dct['au'] = ', '.join( authors )
#                         break
#         if citation_form_dct.get( 'date', '' ).strip() is '':
#             if bibjson_dct.get( 'year', '' ) is not '':
#                 citation_form_dct['date'] = bibjson_dct['year']
#         if citation_form_dct.get( 'id', '' ).strip() is '':
#                 if bibjson_dct.get( 'identifier', '' ) is not '':
#                     for entry in bibjson_dct['identifier']:
#                         if entry.get( 'type', '' ) == 'doi':
#                             citation_form_dct['issn'] = entry['id']
#                             break
#         if citation_form_dct.get( 'pages', '' ).strip() is '':
#             if bibjson_dct.get( 'pages', '' ) is not '':
#                 citation_form_dct['pages'] = bibjson_dct['pages']
#         # TODO: try rfe_dat (oclcnum)
#         log.debug( 'final citation_form_dct, ```%s```' % pprint.pformat(citation_form_dct) )
#         return citation_form_dct

#     def _check_genre( self, querydct ):
#         """ Tries to determine genre. """
#         genre = 'article'
#         if querydct.get('genre') == 'book' or querydct.get('rft.genre') == 'book':
#             genre = 'book'
#         elif len(querydct.get('isbn', '')) > 0 or len(querydct.get('rft:isbn', '')) > 0:
#             genre = 'book'
#         log.debug( 'genre, `%s`' % genre )
#         return genre

#     def _handle_v_list(self, v):
#         """ Handles querydict list values, and checks for a replace.
#             Called by make_form_dct(). """
#         # log.debug( 'initial v, `%s`' % v )
#         if (v) and (v != '') and (type(v)==list):
#             v = v[0]
#         if type(v) == unicode and 'accessionnumber' in v:
#             v = v.replace('<accessionnumber>', '').replace('</accessionnumber>', '')  # for oclc numbers
#         log.debug( 'returned v, `%s`' % v )
#         return v

#     def _handle_k( self, k, v ):
#         """ Handles two key situations.
#             Called by make_form_dct(). """
#         if k == 'id':
#             if v.startswith('doi'):
#                 ( k,v ) = ( 'id', v.replace('doi:', '') )
#         elif k == 'doi':
#             k = 'id'
#         log.debug( '(k,v), `(%s,%s)`' % (k,v) )
#         return ( k,v )

#     # end class CitationFormHelper
