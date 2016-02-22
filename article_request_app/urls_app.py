# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    # ensures user comes from correct 'findit' url, and that user is logged out of shib; then redirects to `login`
    url( r'^check_login/$',  'article_request_app.views.check_login', name='check_login_url' ),

    # shib-protected; checks illiad; then redirects to `illiad`
    url( r'^login/$',  'article_request_app.views.login', name='login_url' ),

    # on GET, displays confirmation button and citation; on POST, submits to illiad; redirects to `confirmation`
    url( r'^illiad/$',  'article_request_app.views.illiad_request', name='illiad_request_url' ),

    # shows confirmation message
    url( r'^confirmation/$',  'article_request_app.views.confirmation', name='confirmation' ),

    # for optional manual logout
    url( r'^logout/$',  'article_request_app.views.logout', name='logout_url' ),

    # displays brief message; redirects user to easyAccess landing page
    url( r'^$',  'article_request_app.views.oops', name='oops_url' ),

    )
