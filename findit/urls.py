# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, url


urlpatterns = patterns(

    '',

    url( r'^citation_form/$', 'findit.views.citation_form', name='citation_form_url' ),

    url( r'^permalink/(?P<permalink_str>.*)/$', 'findit.views.permalink', name='permalink_url' ),

    url( r'^ris_citation/$', 'findit.views.ris_citation', name='ris_url' ),

    url( r'^link360/$', 'findit.views.link360', name='link360_url' ),

    url( r'^my_info/$', 'findit.views.shib_info', name='shib_info_url' ),

    url( r'^$', 'findit.views.findit_base_resolver', name=u'findit_base_resolver_url' ),

)
