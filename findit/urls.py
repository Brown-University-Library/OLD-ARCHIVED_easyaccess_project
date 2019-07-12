# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import url
from findit import views


urlpatterns = [

    url( r'^citation_form/$', views.citation_form, name='citation_form_url' ),

    url( r'^permalink/(?P<permalink_str>.*)/$', views.permalink, name='permalink_url' ),

    url( r'^ris_citation/$', views.ris_citation, name='ris_url' ),

    url( r'^link360/$', views.link360, name='link360_url' ),

    # url( r'^my_info/$', views.shib_info, name='shib_info_url' ),

    # url( r'^info/$', views.info, name='info_url' ),

    url( r'^$', views.findit_base_resolver, name=u'findit_base_resolver_url' ),

    ]
