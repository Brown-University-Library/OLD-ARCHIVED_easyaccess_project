# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls import include, patterns, url
from django.contrib import admin


# from views import ResolveView, Link360View, PermalinkView, UserInfoView,\
#                   ProcessBibView, RequestView, StaffView


urlpatterns = patterns('',

    url( r'^availability/$',  'delivery.views.availability', name=u'availability_url' ),  # if 'Request this' is clicked, goes to 'login'

    url( r'^shib_login/$',  'delivery.views.shib_login', name=u'shib_login_url' ),  # after shib, redirects to behind-the-scenes 'login'

    url( r'^login/$',  'delivery.views.login', name=u'login_url' ),  # after login, redirects to behind-the-scenes 'process_request'
    url( r'^process_request/$',  'delivery.views.process_request', name=u'process_request_url' ),  # after processing, redirects to behind-the-scenes 'shib_logout'
    url( r'^shib_logout/$',  'delivery.views.shib_logout', name=u'shib_logout_url' ),  # after processing, redirects to 'message'
    url( r'^message/$',  'delivery.views.message', name=u'message_url' ),  # endpoint

    # url(r'request$', RequestView.as_view(), name='request'),
    # url(r'^$', ResolveView.as_view(), name='resolve'),

    )

# urlpatterns = patterns('',
#     # url(r'link360/', Link360View.as_view(), name='link360'),  # doesn't seem to do anything in easyArticle
#     # url(r'old', ResolveView.as_view(), name='orig'),
#     #url(r'p(?P<tiny>.*)|permalink', PermalinkView.as_view(), name='short'),
#     # url(r'get/(?P<tiny>.*)/', PermalinkView.as_view(), name='short'),
#     # url(r'permalink', PermalinkView.as_view(), name='permalink-post'),
#     # url(r'process', ProcessBibView.as_view(), name='process'),    # doesn't seem to do anything in easyArticle
#     # url(r'request/(?P<tiny>.*)/', RequestView.as_view(), name='request-short'),
#     # url(r'request$', RequestView.as_view(), name='request'),
#     # url(r'staff', StaffView.as_view(), name='staff'),  # doesn't seem to do anything in easyArticle
#     # url(r'user-info', UserInfoView.as_view(), name='user-info'),    # doesn't seem to do anything in easyArticle
#     url(r'^$', ResolveView.as_view(), name='resolve'),
#     # url( r'^$',  'delivery.views.base_resolver', name=u'delivery_base_resolver_url' ),  # will be new
#     )

# urlpatterns = patterns('',
#     #citation form
#     url(r'link360/', Link360View.as_view(), name='link360'),
#     url(r'old', ResolveView.as_view(), name='orig'),
#     #url(r'p(?P<tiny>.*)|permalink', PermalinkView.as_view(), name='short'),
#     url(r'get/(?P<tiny>.*)/', PermalinkView.as_view(), name='short'),
#     url(r'permalink', PermalinkView.as_view(), name='permalink-post'),
#     url(r'process', ProcessBibView.as_view(), name='process'),
#     url(r'request/(?P<tiny>.*)/', RequestView.as_view(), name='request-short'),
#     url(r'request$', RequestView.as_view(), name='request'),
#     url(r'staff', StaffView.as_view(), name='staff'),
#     url(r'user-info', UserInfoView.as_view(), name='user-info'),
#     url(r'^$', ResolveView.as_view(), name='resolve'),
# )
