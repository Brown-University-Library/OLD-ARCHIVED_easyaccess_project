# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json,logging, pprint, re, urlparse
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.log import dictConfig
from findit import forms

# import requests
# from . import forms, summon
# from .app_settings import DB_SORT_BY, DB_PUSH_TOP, DB_PUSH_BOTTOM
# from .app_settings import PRINT_PROVIDER
# from .models import PrintTitle
# from django.core.urlresolvers import reverse
# from py360link2 import get_sersol_data, Resolved


# CURRENT_YEAR = datetime.now().year


dictConfig( settings.LOGGING )
log = logging.getLogger('access')


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
        citation_form_dct = self.make_form_dct( request.GET )
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

    ## helpers

    def make_form_dct(self, querydct):
        """ Transfers metadata from openurl to dct for citation-linker form.
            Called by build_context_from_url(). """
        citation_form_dct = {}
        for k,v in querydct.items():
            if (v) and (v != '') and (type(v)==list):
                v = v[0]
            if k == 'id':
                if v.startswith('doi'):
                    ( k,v ) = ( 'doi', v.replace('doi:', '') )
            v = v.replace('<accessionnumber>', '').replace('</accessionnumber>', '')  # for oclc numbers
            citation_form_dct[k] = v
        log.debug( 'citation_form_dct, ```%s```' % pprint.pformat(citation_form_dct) )
        return citation_form_dct

    def make_form_type( self, dct ):
        """ Tries to get the default form right.
            Called by build_context_from_url() """
        form_type = 'article'
        if dct.get('isbn', '') is not '' and dct.get('issn', '') is '':
            form_type = 'book'
        log.debug( 'form_type, `%s`' % form_type )
        return form_type

    # end class CitationFormHelper
