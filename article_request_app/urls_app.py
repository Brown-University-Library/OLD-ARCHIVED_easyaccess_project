# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^illiad/$',  'article_request_app.views.illiad_request', name='illiad_request_url' ),

    url( r'^confirmation/$',  'article_request_app.views.confirmation', name='confirmation' ),

    url( r'^$',  RedirectView.as_view(pattern_name='request_url') ),

    )
