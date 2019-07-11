# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from findit import views as findit_views
from status_app import views as status_views


admin.autodiscover()


urlpatterns = [

    url( r'^admin/', include(admin.site.urls) ),

    ## -- find
    url( r'^find/info/$', RedirectView.as_view(pattern_name='status_version_url') ),  # remove after 3 months, on 2019-October-12
    url( r'^find/', include('findit.urls', namespace='findit') ),  # resolver -- enhances, finds, redirects

    ## -- book and article handling
    url( r'^borrow/', include('delivery.urls', namespace='delivery') ),  # submits to easyBorrow
    url( r'^article_request/', include('article_request_app.urls_app', namespace='article_request') ),  # article-requests

    ## -- book and article handling
    url( r'^bul_search/$', findit_views.bul_search, name='bul_search_url' ),

    ## -- support urls
    url( r'^version/$', status_views.version, name='status_version_url' ),
    url( r'^error_check/$', status_views.error_check, name='status_error_check_url' ),

    ## -- other
    url( r'^$', RedirectView.as_view(pattern_name='findit:findit_base_resolver_url') ),

    ## -- old, for reference
    # url( r'^bul_link/', include('bul_link.urls', namespace='bul_link') ),  # will likely retire

    ]

## for 500 errors
handler500 = 'findit.views.server_error'
