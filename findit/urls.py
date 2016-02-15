# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from app_settings import PERMALINK_PREFIX
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls import include, patterns, url
from views import CitationFormView, JstorView, MicrosoftView, RequestView, SummonView, UserView


urlpatterns = patterns('',

    url( r'^citation-form/$',  CitationFormView.as_view(), name='citation-form-view' ),

    # url( r'^request/(?P<resource>[0-9]+)/$',  RequestView.as_view(), name='request-view' )  # might be needed for illiad requests, but I'd think they would go to /borrow

    # url( r'^mas/$',  MicrosoftView.as_view(), name='microsoft-view' ),

    # url( r'^jstor/$',  JstorView.as_view(), name='jstor-view' ),

    # url( r'^user/$',  UserView.as_view(), name='user-view' ),

    #Handle permalinks or OpenURL lookups
    url( r'^get/%s(?P<tiny>.*)/$' % PERMALINK_PREFIX,  'findit.views.tiny_resolver', name=u'permalink_url' ),
    url( r'^get/(?P<id_type>pmid|doi)/(?P<id_value>.*)/$',  SummonView.as_view(), name='summon-view' ),

    url( r'^$',  'findit.views.findit_base_resolver', name=u'findit_base_resolver_url' ),

    )
