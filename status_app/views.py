# -*- coding: utf-8 -*-

from __future__ import unicode_literals

## stdlib
import datetime, json, logging, pprint

## other
from status_app.lib import version_helper
from django.conf import settings as project_settings
from django.http import HttpResponse
# import bibjsontools
# from . import app_settings
# from .classes import view_info_helper
# from .classes.citation_form_helper import CitationFormHelper
# from .classes.findit_resolver_helper import FinditResolver
# from .classes.findit_resolver_helper import RisHelper
# from .classes.permalink_helper import Permalink
# from bibjsontools import ris as bibjsontools_ris
# from django.conf import settings
# from django.core.urlresolvers import reverse


def version( request ):
    """ Returns basic data including branch & commit. """
    # return HttpResponse( 'info coming' )
    rq_now = datetime.datetime.now()
    commit = version_helper.get_commit()
    branch = version_helper.get_branch()
    info_txt = commit.replace( 'commit', branch )
    resp_now = datetime.datetime.now()
    taken = resp_now - rq_now
    context_dct = version_helper.make_context( request, rq_now, info_txt, taken )
    output = json.dumps( context_dct, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


def error_check( request ):
    """ For checking that admins receive error-emails. """
    if project_settings.DEBUG == True:
        1/0
    else:
        return HttpResponseNotFound( '<div>404 / Not Found</div>' )
