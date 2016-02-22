# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^check_login/$',  'article_request_app.views.check_login', name='check_login_url' ),
    # ensures user comes from correct 'findit' url, and that user is logged out of shib; then redirects to `login`

    url( r'^login/$',  'article_request_app.views.login', name='login_url' ),
    # shib-protected; checks illiad for new-user or blocked; if happy, redirects to `illiad`

    url( r'^illiad/$',  'article_request_app.views.illiad_request', name='illiad_request_url' ),
    # on GET, displays confirmation button and citation; on POST, submits to illiad; redirects to `confirmation`

    url( r'^confirmation/$',  'article_request_app.views.confirmation', name='confirmation' ),
    # shows confirmation message

    url( r'^logout/$',  'article_request_app.views.logout', name='logout_url' ),
    # for optional manual logout

    url( r'^$',  'article_request_app.views.oops', name='oops_url' ),
    # displays brief message; redirects user to easyAccess landing page

    )
