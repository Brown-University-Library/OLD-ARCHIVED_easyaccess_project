# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from article_request_app import views
from django.conf.urls import url


urlpatterns = [

    url( r'^shib_login/$', views.shib_login, name='shib_login_url' ),
    ## after shib-login; redirects to `login_handler`.

    url( r'^login_handler/$', views.login_handler, name='login_handler_url' ),
    ## ensures user comes from correct 'findit' url; checks illiad for new-user or blocked; if happy, redirects to `illiad`, otherwise to `message` with error.

    url( r'^illiad/$', views.illiad_request, name='illiad_request_url' ),
    ## displays confirmation 'Submit' button and citation; submission hits 'illiad_handler'

    url( r'^illiad_handler/$', views.illiad_handler, name='illiad_handler_url' ),
    ## behind-the-scenes, submits request to illiad, then redirects to message_url

    url( r'^shib_logout/$', views.shib_logout, name=u'shib_logout_url' ),
    ## after shib_logout, redirects to 'message'

    url( r'^message/$', views.message, name='message_url' ),
    ## shows confirmation or problem message

    ]
