# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.views.generic import TemplateView
# from django.conf.urls.defaults import *
from django.conf.urls import include, patterns, url

from views import ResolveView
from app_settings import PERMALINK_PREFIX


urlpatterns = patterns('',

    #Handle permalinks or OpenURL lookups
    url( r'^get/%s(?P<tiny>.*)/$' % PERMALINK_PREFIX,  ResolveView.as_view(), name='permalink_view' ),

    url( r'^$',  ResolveView.as_view(), name='resolve_view' ),

    )
