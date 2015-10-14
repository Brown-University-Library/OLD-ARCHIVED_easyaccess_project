# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import django
from django.conf.urls import patterns, url
from views import ShibbolethView, ShibbolethLogoutView, ShibbolethLoginView


urlpatterns = patterns('',
    url( r'^your_shib_info/$', 'shibboleth.views.info', name='shib_info_url' ),
    url( r'^login/$', ShibbolethLoginView.as_view(), name='login'),
    url( r'^logout/$', ShibbolethLogoutView.as_view(), name='logout'),
    url( r'^$', ShibbolethView.as_view(), name='info' ),
    )
