# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
# from .models import Validator, ViewHelper
from django.shortcuts import get_object_or_404, render

log = logging.getLogger(__name__)
# validator = Validator()
# view_helper = ViewHelper()


def check_login( request ):
    return HttpResponse( 'check_login-coming' )


def login( request ):
    return HttpResponse( 'login-coming' )


def illiad_request( request ):
    context = {}
    resp = render( request, 'article_request_app/request.html', context )
    return resp


def confirmation( request ):
    return HttpResponse( 'confirmation-coming' )


def logout( request ):
    return HttpResponse( 'logout-coming' )


def oops( request ):
    return HttpResponse( 'oops-coming' )
