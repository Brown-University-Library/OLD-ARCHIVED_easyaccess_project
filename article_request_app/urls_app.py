# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^shib_login/$',  'article_request_app.views.shib_login', name='shib_login_url' ),
    # after shib-login; redirects to `login_handler`.

    url( r'^login_handler/$',  'article_request_app.views.login_handler', name='login_handler_url' ),
    # ensures user comes from correct 'findit' url; checks illiad for new-user or blocked; if happy, redirects to `illiad`, otherwise to `message` with error.

    url( r'^illiad/$',  'article_request_app.views.illiad_request', name='illiad_request_url' ),
    # displays confirmation 'Submit' button and citation; submission hits 'illiad_handler'

    url( r'^illiad_handler/$',  'article_request_app.views.illiad_handler', name='illiad_handler_url' ),
    # behind-the-scenes, submits request to illiad, then redirects to message_url

    # url( r'^logout/$',  'article_request_app.views.logout', name='logout_url' ),
    # for optional manual logout

    url( r'^message/$',  'article_request_app.views.message', name='message_url' ),
    # shows confirmation or problem message

    )
