# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',


    url( r'^login/$',  'article_request_app.views.login', name='login_url' ),
    # ensures user comes from correct 'findit' url; then forces login; then checks illiad for new-user or blocked; if happy, redirects to `illiad`, otherwise to `oops`.

    url( r'^illiad/$',  'article_request_app.views.illiad_request', name='illiad_request_url' ),
    # on GET, displays confirmation button and citation; on POST, submits to illiad; redirects to `confirmation`

    url( r'^confirmation/$',  'article_request_app.views.confirmation', name='confirmation_url' ),
    # shows confirmation message

    url( r'^logout/$',  'article_request_app.views.logout', name='logout_url' ),
    # for optional manual logout

    url( r'^$',  'article_request_app.views.oops', name='oops_url' ),
    # displays brief message; redirects user to easyAccess landing page

    )
