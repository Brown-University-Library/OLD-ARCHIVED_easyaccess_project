import logging

import requests
from django.core.cache import cache
from django.core.urlresolvers import reverse
from findit import app_settings


log = logging.getLogger('access')


def prep_pattern_header( feedback_url, easy_type ) -> str:
    log.debug( f'feedback_url, ```{feedback_url}```' )
    log.debug( f'easy_type, ```{easy_type}```' )
    header_html = grab_pattern_header()
    if easy_type != 'easyAccess':
        easy_type = f'easyAccess → {easy_type}'
    header_html = header_html.replace( 'DYNAMIC__TITLE', easy_type )
    header_html = header_html.replace( 'DYNAMIC__SITE', reverse('findit:findit_base_resolver_url') )
    header_html = header_html.replace( 'DYNAMIC__FEEDBACK', feedback_url )
    log.debug( f'returning header_html, ```{header_html}```' )
    log.debug( f'type(header_html), `{type(header_html)}`' )
    return header_html


def grab_pattern_header() -> str:
    """ Prepares html for header. """
    cache_key = 'pattern_header'
    header_html = cache.get( cache_key, None )
    if header_html:
        log.debug( 'pattern-header in cache' )
    else:
        log.debug( 'pattern-header not in cache' )
        r = requests.get( app_settings.PATTERN_HEADER_URL )
        header_html = r.content.decode( 'utf8' )
        cache.set( cache_key, header_html, app_settings.PATTERN_LIB_CACHE_TIMEOUT )
    return header_html

