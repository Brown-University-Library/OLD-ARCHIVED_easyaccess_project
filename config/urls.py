# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView


admin.autodiscover()


urlpatterns = [

    url( r'^admin/', include(admin.site.urls) ),

    url( r'^user/', include('shibboleth.urls', namespace='shibboleth') ),  # will likely retire

    url( r'^borrow/', include('delivery.urls', namespace='delivery') ),  # submits to easyBorrow

    url( r'^find/', include('findit.urls', namespace='findit') ),  # resolver -- enhances, finds, redirects

    url( r'^article_request/', include('article_request_app.urls_app', namespace='article_request') ),  # article-requests

    url( r'^bul_link/', include('bul_link.urls', namespace='bul_link') ),  # will likely retire

    url( r'^$',  RedirectView.as_view(url='easyaccess/find/', permanent=True) ),  # will likely retire
    ]

## for 500 errors
handler500 = 'findit.views.server_error'
