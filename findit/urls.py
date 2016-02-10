# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.views.generic import TemplateView
# from django.conf.urls.defaults import *
from django.conf.urls import include, patterns, url

# from views import Resolver, CitationFormView, RequestView,\
#                   UserView, MicrosoftView, JstorView, SummonView

from views import CitationFormView, RequestView, UserView, MicrosoftView, JstorView, SummonView

from app_settings import PERMALINK_PREFIX


urlpatterns = patterns('',

    url( r'^citation-form/$',  CitationFormView.as_view(), name='citation-form-view' ),

    url( r'^request/(?P<resource>[0-9]+)/$',  RequestView.as_view(), name='request-view' ),

    url( r'^mas/$',  MicrosoftView.as_view(), name='microsoft-view' ),

    url( r'^jstor/$',  JstorView.as_view(), name='jstor-view' ),

    url( r'^user/$',  UserView.as_view(), name='user-view' ),

    #Handle permalinks or OpenURL lookups
    # url( r'^get/%s(?P<tiny>.*)/$' % PERMALINK_PREFIX,  Resolver.as_view(), name='permalink-view' ),
    url( r'^get/%s(?P<tiny>.*)/$' % PERMALINK_PREFIX,  'findit.views.tiny_resolver', name=u'permalink_url' ),

    url( r'^get/(?P<id_type>pmid|doi)/(?P<id_value>.*)/$',  SummonView.as_view(), name='summon-view' ),

    # url( r'^$',  Resolver.as_view(), name='resolver-view' ),
    url( r'^$',  'findit.views.findit_base_resolver', name=u'findit_base_resolver_url' ),

    )

# urlpatterns = patterns('',
#     #citation form
#     url(r'^citation-form/$',
#         CitationFormView.as_view(),
#         name='citation-form-view'),
#     url(r'^request/(?P<resource>[0-9]+)/$',
#         RequestView.as_view(),
#         name='request-view'),
#     url(r'^mas/$',
#         MicrosoftView.as_view(),
#         name='microsoft-view'),
#     url(r'^jstor/$',
#         JstorView.as_view(),
#         name='jstor-view'),
#     url(r'^user/$',
#         UserView.as_view(),
#         name='user-view'),
#     #Handle permalinks or OpenURL lookups
#     url(r'^get/%s(?P<tiny>.*)/$' % PERMALINK_PREFIX,
#             Resolver.as_view(),
#             name='permalink-view'),
#     url(r'^get/(?P<id_type>pmid|doi)/(?P<id_value>.*)/$',
#         SummonView.as_view(),
#         name='summon-view'),
#     url(r'^',
#         Resolver.as_view(),
#         name='resolver-view'),
# )
