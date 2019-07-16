# -*- coding: utf-8 -*-

import logging, pprint
import bibjsontools
from django.core.urlresolvers import reverse
from django.shortcuts import render
from findit import app_settings, forms
from findit.classes.permalink_helper import Permalink


log = logging.getLogger('access')
shortlink_helper = Permalink()


class CitationFormDctMaker( object ):
    """ Converts django querystring-object to form-dct. """

    def make_form_dct( self, querydct ):
        """ Transfers metadata from openurl to dct for citation-linker form.
            Called by build_context_from_url(). """
        log.debug( 'querydct, ```%s```' % pprint.pformat(querydct) )
        bibjson_dct = self.make_bibjson_dct( querydct )
        citation_form_dct = self.make_initial_citation_form_dct( querydct )
        genre = self.check_genre( querydct )
        if genre == 'book':
            citation_form_dct = self.update_book_fields( citation_form_dct )
        else:  # article
            citation_form_dct = self.update_article_fields( bibjson_dct, citation_form_dct )
        citation_form_dct = self.update_common_fields( bibjson_dct, citation_form_dct )
        log.debug( 'final citation_form_dct, ```%s```' % pprint.pformat(citation_form_dct) )
        return citation_form_dct

    def make_bibjson_dct( self, querydct ):
        """ Transforms querystring into bibjson dictionary.
            Called by make_form_dct() """
        qstring = ''
        for k, v in querydct.items():
            qstring = qstring + '%s=%s&' % (k, v)
        qstring = qstring[0:-1]
        log.debug( 'qstring, `%s`' % qstring )
        log.debug( 'type(qstring), `%s`' % type(qstring) )
        bibjson_dct = bibjsontools.from_openurl( qstring )
        log.debug( 'bibjson_dct, ```%s```' % pprint.pformat(bibjson_dct) )
        return bibjson_dct

    def make_initial_citation_form_dct( self, querydct ):
        """ Makes initial citation_form_dct from key-value pairs.
            Called by make_form_dct() """
        citation_form_dct = {}
        for k, v in querydct.items():
            # log.debug( 'querydict (k,v), `(%s,%s)`' % (k,v) )
            v = self.handle_v_list( v )
            ( k, v ) = self.handle_k( k, v )
            citation_form_dct[k] = v
        log.debug( 'initial_citation_form_dct, ```%s```' % pprint.pformat(citation_form_dct) )
        return citation_form_dct

    def check_genre( self, querydct ):
        """ Tries to determine genre. """
        genre = 'article'
        if querydct.get('genre') == 'book' or querydct.get('rft.genre') == 'book':
            genre = 'book'
        elif len(querydct.get('isbn', '')) > 0 or len(querydct.get('rft:isbn', '')) > 0:
            genre = 'book'
        log.debug( 'genre, `%s`' % genre )
        return genre

    def update_book_fields( self, citation_form_dct ):
        """ Populates book-specific fields: btitle, isbn, pub, place, spage, epage.
            Called by make_form_dct() """
        log.debug( 'in book handler')
        if citation_form_dct.get('btitle', None) is None:
            citation_form_dct['btitle'] = citation_form_dct.get('title', None)
        if citation_form_dct.get('pub', None) is None:
            citation_form_dct['pub'] = citation_form_dct.get('rft.pub', None)
        if citation_form_dct.get('place', None) is None:
            citation_form_dct['place'] = citation_form_dct.get('rft.place', None)
        return citation_form_dct

    def update_article_fields( self, bibjson_dct, citation_form_dct ):
        """ Updates article-specific fields: atitle, jtitle, issn, pmid, volume, issue
            Called by: make_form_dct() """
        citation_form_dct['atitle'] = self._make_article_atitle( bibjson_dct, citation_form_dct )
        citation_form_dct['jtitle'] = self._make_article_jtitle( bibjson_dct, citation_form_dct )
        citation_form_dct['issn'] = self._make_article_issn( bibjson_dct, citation_form_dct )
        if citation_form_dct.get('pmid', '').strip() == '':
            pass  # TODO: implement
        if citation_form_dct.get('volume', '').strip() == '':
            citation_form_dct['volume'] = bibjson_dct.get( 'volume', '' )
        if citation_form_dct.get('issue', '').strip() == '':
            citation_form_dct['issue'] = bibjson_dct.get( 'issue', '' )
        return citation_form_dct

    def _make_article_atitle( self, bibjson_dct, citation_form_dct ):
        """ Makes article atitle.
            Called by update_article_fields() """
        atitle = citation_form_dct.get('atitle', '').strip()
        if atitle == '':
            atitle = bibjson_dct.get( 'title', '' )
        return atitle

    def _make_article_jtitle( self, bibjson_dct, citation_form_dct ):
        """ Makes article jtitle.
            Called by update_article_fields() """
        jtitle = citation_form_dct.get('jtitle', '').strip()
        if jtitle == '':
            if bibjson_dct.get( 'journal', '' ) is not '':
                if bibjson_dct['journal'].get( 'name', '' ) is not '':
                    jtitle = bibjson_dct['journal']['name']
        return jtitle

    def _make_article_issn( self, bibjson_dct, citation_form_dct ):
        """ Makes article issn.
            Called by update_article_fields() """
        issn = citation_form_dct.get('issn', '').strip()
        if issn == '':
            if bibjson_dct.get( 'identifier', '' ) is not '':
                for entry in bibjson_dct['identifier']:
                    if entry.get( 'type', '' ) == 'issn':
                        issn = entry['id']
                        break
        return issn

    def update_common_fields( self, bibjson_dct, citation_form_dct ):
        """ Populates common fields: 'au', 'date', 'id', 'pages', 'rfe_dat'.
            Called by make_form_dct() """
        citation_form_dct['au'] = self._make_common_au( bibjson_dct, citation_form_dct )
        citation_form_dct['date'] = self._make_common_date( bibjson_dct, citation_form_dct )
        citation_form_dct['id'] = self._make_common_id( bibjson_dct, citation_form_dct )
        citation_form_dct['pages'] = self._make_common_pages( bibjson_dct, citation_form_dct )
        # TODO: try rfe_dat (oclcnum)
        return citation_form_dct

    def _make_common_au( self, bibjson_dct, citation_form_dct ):
        """ Makes common au data (author).
            Called by update_common_fields() """
        au = citation_form_dct.get('au', '').strip()
        if au == '':
            if bibjson_dct.get( 'author', '' ) is not '':
                authors = []
                for entry in bibjson_dct['author']:
                    if entry.get( 'name', '' ) is not '':
                        authors.append( entry['name'] )
                        au = ', '.join( authors )
                        break
        return au

    def _make_common_date( self, bibjson_dct, citation_form_dct ):
        """ Makes common date.
            Called by update_common_fields() """
        date = citation_form_dct.get( 'date', '' ).strip()
        if date is '':
            if bibjson_dct.get( 'year', '' ) is not '':
                date = bibjson_dct['year']
        return date

    def _make_common_pages( self, bibjson_dct, citation_form_dct ):
        """ Makes common pages field.
            Called by update_common_fields() """
        pages = citation_form_dct.get( 'pages', '' ).strip()
        if pages is '':
            if bibjson_dct.get( 'pages', '' ) is not '':
                pages = bibjson_dct['pages'].replace( ' ', '' )
        else:
            pages = citation_form_dct['pages'].replace( ' ', '' )
        return pages

    def _make_common_id( self, bibjson_dct, citation_form_dct ):
        """ Makes common id field.
            Called by update_common_fields() """
        id_field = citation_form_dct.get( 'id', '' ).strip()
        if id_field is '':
                if bibjson_dct.get( 'identifier', '' ) is not '':
                    for entry in bibjson_dct['identifier']:
                        if entry.get( 'type', '' ) == 'doi':
                            id_field = entry['id'].replace( 'doi:', '' )
                            break
        return id_field

    def handle_v_list(self, v):
        """ Handles querydict list values, and checks for a replace.
            Called by make_form_dct(). """
        # log.debug( 'initial v, `%s`' % v )
        if (v) and (v != '') and (type(v) == list):
            v = v[0]
        if type(v) == str and 'accessionnumber' in v:
            v = v.replace('<accessionnumber>', '').replace('</accessionnumber>', '')  # for oclc numbers
        log.debug( 'returned v, `%s`' % v )
        return v

    def handle_k( self, k, v ):
        """ Handles two key situations.
            Called by make_form_dct(). """
        if k == 'id':
            if v.startswith('doi'):
                ( k, v ) = ( 'id', v.replace('doi:', '') )
        elif k == 'doi':
            k = 'id'
        log.debug( '(k, v), `(%s, %s)`' % (k, v) )
        return ( k, v )

    ## end class CitationFormDictMaker()


class CitationFormHelper( object ):
    """ Handles views.citation_form() calls. """

    def __init__(self):
        self.log_id = ''

    def build_simple_context( self, request ):
        """ Prepares simple GET context.
            Called by views.citation_form() """
        context = {
            u'article_form': forms.ArticleForm,
            u'book_form': forms.BookForm,
            u'form_type': u'article',
            u'problem_link': u'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://127.0.0.1/citation-form/&entry_4=127.0.0.1',
        }
        # log.debug( 'context, `%s`' % context )
        log.debug( '`{id}` context, ```{val}```'.format(id=self.log_id, val=pprint.pformat(context)) )
        return context

    def build_context_from_url( self, request ):
        """ Populates form from url.
            Called by views.citation_form() """
        # log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
        log.debug( '`{id}` request.__dict__, ```{val}```'.format(id=self.log_id, val=pprint.pformat(request.__dict__)) )
        form_dct_maker = CitationFormDctMaker()
        citation_form_dct = form_dct_maker.make_form_dct( request.GET )
        log.info( '`{id}` citation_form_dct, ```{val}```'.format(id=self.log_id, val=pprint.pformat(citation_form_dct)) )
        querystring = request.META.get('QUERY_STRING', '')

        shortlink_path = shortlink_helper.make_permalink(
            referrer=request.GET.get('rfr_id', ''), qstring=request.META.get('QUERY_STRING', ''), scheme=request.scheme, host=request.get_host(), path=reverse('findit:citation_form_url')
        )['permalink']
        log.debug( 'shortlink_path, ```%s```' % shortlink_path )
        full_shortlink_url = '%s://%s%s' % ( request.scheme, request.get_host(), shortlink_path )
        log.debug( 'full_shortlink_url, ```%s```' % full_shortlink_url )

        context = {
            u'article_form': forms.ArticleForm(citation_form_dct),
            u'book_form': forms.BookForm(citation_form_dct),
            u'form_type': self.make_form_type( citation_form_dct ),
            u'problem_link': app_settings.PROBLEM_URL % ( full_shortlink_url, request.META.get('REMOTE_ADDR', 'unknown') ),
        }
        # log.debug( '`{id}` context, ```{val}```'.format(id=self.log_id, val=pprint.pformat(context)) )
        log.debug( '`%s` context, ```%s```' % (self.log_id, pprint.pformat(context)) )
        return context

    # def build_context_from_url( self, request ):
    #     """ Populates form from url.
    #         Called by views.citation_form() """
    #     # log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
    #     log.debug( '`{id}` request.__dict__, ```{val}```'.format(id=self.log_id, val=pprint.pformat(request.__dict__)) )
    #     form_dct_maker = CitationFormDctMaker()
    #     citation_form_dct = form_dct_maker.make_form_dct( request.GET )
    #     log.info( '`{id}` citation_form_dct, ```{val}```'.format(id=self.log_id, val=pprint.pformat(citation_form_dct)) )
    #     context = {
    #         u'article_form': forms.ArticleForm(citation_form_dct),
    #         u'book_form': forms.BookForm(citation_form_dct),
    #         u'form_type': self.make_form_type( citation_form_dct ),
    #         u'problem_link': 'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://127.0.0.1/citation-form/&entry_4=127.0.0.1',
    #     }
    #     # log.debug( 'context, `%s`' % context )
    #     log.debug( '`{id}` context, ```{val}```'.format(id=self.log_id, val=pprint.pformat(context)) )
    #     return context

    def build_get_response( self, request, context ):
        """ Prepares GET response
            Called by views.citation_form() """
        resp = render( request, 'findit_templates/citation_linker_2.html', context )
        # log.debug( 'returning response' )
        log.debug( '`{id}` returning response'.format(id=self.log_id) )
        return resp

    def make_form_type( self, dct ):
        """ Tries to get the default form right.
            Called by build_context_from_url() """
        form_type = 'article'
        if dct.get('isbn', '') is not '' and dct.get('issn', '') is '':
            form_type = 'book'
        elif dct.get('genre', '') == 'book':
            form_type = 'book'
        # log.debug( 'form_type, `%s`' % form_type )
        log.debug( '`{id}` form_type, ```{val}```'.format(id=self.log_id, val=form_type) )
        return form_type

    ## end class CitationFormHelper()
