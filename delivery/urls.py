from django.conf import settings
from django.views.generic import TemplateView
# from django.conf.urls.defaults import *
from django.conf.urls import include, patterns, url
from django.contrib import admin


from views import ResolveView, Link360View, PermalinkView, UserInfoView,\
                  ProcessBibView, RequestView, StaffView


urlpatterns = patterns('',
    #citation form
    url(r'link360/', Link360View.as_view(), name='link360'),
    url(r'old', ResolveView.as_view(), name='orig'),
    #url(r'p(?P<tiny>.*)|permalink', PermalinkView.as_view(), name='short'),
    url(r'get/(?P<tiny>.*)/', PermalinkView.as_view(), name='short'),
    url(r'permalink', PermalinkView.as_view(), name='permalink-post'),
    url(r'process', ProcessBibView.as_view(), name='process'),
    url(r'request/(?P<tiny>.*)/', RequestView.as_view(), name='request-short'),
    url(r'request$', RequestView.as_view(), name='request'),
    url(r'staff', StaffView.as_view(), name='staff'),
    url(r'user-info', UserInfoView.as_view(), name='user-info'),
    url(r'^$', ResolveView.as_view(), name='resolve'),
    )

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
