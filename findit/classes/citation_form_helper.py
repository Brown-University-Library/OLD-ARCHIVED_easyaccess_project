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

    def build_context( self, request ):
        """ Prepares GET context.
            Called by views.citation_form() """
        context = {
            u'article_form': forms.ArticleForm,
            u'book_form': forms.BookForm,
            # u'direct_link': None,
            u'form_type': u'article',
            # u'openurl': '',
            u'problem_link': u'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://127.0.0.1/citation-form/&entry_4=127.0.0.1',
            }
        log.debug( 'context, `%s`' % context )
        return context

    def build_get_response( self, request, context ):
        """ Prepares GET response
            Called by views.citation_form() """
        resp = render( request, 'findit/citation_linker.html', context )
        log.debug( 'returning response' )
        return resp
