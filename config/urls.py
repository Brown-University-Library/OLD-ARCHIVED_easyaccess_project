# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView


admin.autodiscover()


urlpatterns = [
    url( r'^admin/', include(admin.site.urls) ),
    url( r'^user/', include('shibboleth.urls', namespace='shibboleth') ),
    url( r'^borrow/', include('delivery.urls', namespace='delivery') ),
    url( r'^find/', include('findit.urls', namespace='findit') ),

    url( r'^bul_link/', include('bul_link.urls', namespace='bul_link') ),

    url( r'^$',  RedirectView.as_view(url='find/', permanent=True) ),
    ]

## for 500 errors
handler500 = 'findit.views.server_error'
