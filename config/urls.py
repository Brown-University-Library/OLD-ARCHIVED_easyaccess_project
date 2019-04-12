# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from findit import views as findit_views


admin.autodiscover()


urlpatterns = [

    url( r'^admin/', include(admin.site.urls) ),

    url( r'^borrow/', include('delivery.urls', namespace='delivery') ),  # submits to easyBorrow

    url( r'^find/', include('findit.urls', namespace='findit') ),  # resolver -- enhances, finds, redirects

    url( r'^article_request/', include('article_request_app.urls_app', namespace='article_request') ),  # article-requests

    # url( r'^bul_link/', include('bul_link.urls', namespace='bul_link') ),  # will likely retire

    url( r'^bul_search/$', findit_views.bul_search, name='bul_search_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='findit:findit_base_resolver_url') ),

    ]

## for 500 errors
handler500 = 'findit.views.server_error'
