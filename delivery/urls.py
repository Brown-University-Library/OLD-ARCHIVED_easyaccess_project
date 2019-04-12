# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.views.generic import TemplateView
# from django.conf.urls import include, patterns, url
from django.conf.urls import include, url
from django.contrib import admin
from delivery import views


urlpatterns = [

    url( r'^availability/$',  views.availability, name=u'availability_url' ),
    # main landing page -- if 'Request this' appears and is clicked, goes to 'shib_login'

    url( r'^shib_login/$',  views.shib_login, name=u'shib_login_url' ),
    # after shib_login, redirects to behind-the-scenes 'login_handler'

    url( r'^login_handler/$',  views.login_handler, name=u'login_handler_url' ),
    # after login_handler, redirects to behind-the-scenes 'process_request'

    url( r'^process_request/$',  views.process_request, name=u'process_request_url' ),
    # after processing, redirects to behind-the-scenes 'shib_logout'

    url( r'^shib_logout/$',  views.shib_logout, name=u'shib_logout_url' ),
    # after shib_logout, redirects to 'message'

    url( r'^message/$',  views.message, name=u'message_url' ),
    # endpoint

    ]
