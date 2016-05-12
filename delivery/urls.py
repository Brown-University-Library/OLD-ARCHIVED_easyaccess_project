# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls import include, patterns, url
from django.contrib import admin


urlpatterns = patterns('',

    url( r'^availability/$',  'delivery.views.availability', name=u'availability_url' ),
    # main landing page -- if 'Request this' appears and is clicked, goes to 'shib_login'

    url( r'^shib_login/$',  'delivery.views.shib_login', name=u'shib_login_url' ),
    # after shib_login, redirects to behind-the-scenes 'login_handler'

    url( r'^login_handler/$',  'delivery.views.login_handler', name=u'login_handler_url' ),
    # after login_handler, redirects to behind-the-scenes 'process_request'

    url( r'^process_request/$',  'delivery.views.process_request', name=u'process_request_url' ),
    # after processing, redirects to behind-the-scenes 'shib_logout'

    url( r'^shib_logout/$',  'delivery.views.shib_logout', name=u'shib_logout_url' ),
    # after shib_logout, redirects to 'message'

    url( r'^message/$',  'delivery.views.message', name=u'message_url' ),
    # endpoint

    )
