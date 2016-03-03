# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, pprint
from urllib import quote

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


#Logout settings.
from shibboleth.app_settings import LOGOUT_URL, LOGOUT_REDIRECT_URL, LOGOUT_SESSION_KEY


#logging
import logging
# from django.utils.log import dictConfig
# dictConfig(settings.LOGGING)
alog = logging.getLogger('access')


def info( request ):
    """ Returns user shib info. """
    alog.debug( 'starting shibboleth.views.info()' )
    output_dct = {}
    for ( key, val ) in request.META.items():
        # alog.debug( 'key is `%s`; type(val) is `%s`' % (key, type(val)) )
        # if ( 'HTTP_SHIBBOLETH' in key ) and ( type(val) in [bool, int, str, unicode] ) and ( 'session' not in key.lower() ):
        if ( 'Shibboleth-' in key ) and ( type(val) in [bool, int, str, unicode] ) and ( 'session' not in key.lower() ):
            output_dct[key] = val
            if key = 'Shibboleth-isMemberOf':
                output_dct['Shibboleth-isMemberOf'] = output_dct['Shibboleth-isMemberOf'].split(';')
        else:
            alog.debug( 'skipping key, `%s` and val, `%s`' % (key, unicode(repr(val))) )

    output = json.dumps( output_dct, sort_keys=True, indent=2 )
    # output = pprint.pformat( rm )
    return HttpResponse( output, content_type=u'application/json; charset=utf-8' )


class ShibbolethView(TemplateView):
    """
    This is here to offer a Shib protected page that we can
    route users through to login.
    """
    template_name = 'shibboleth/user_info.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Django docs say to decorate the dispatch method for
        class based views.
        https://docs.djangoproject.com/en/dev/topics/auth/
        """
        return super(ShibbolethView, self).dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        """Process the request."""
        next = self.request.GET.get('next', None)
        if next is not None:
            return redirect(next)
        return super(ShibbolethView, self).get(request)

    def get_context_data(self, **kwargs):
        context = super(ShibbolethView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class ShibbolethLoginView(TemplateView):
    """
    Pass the user to the Shibboleth login page.
    Some code borrowed from:
    https://github.com/stefanfoulis/django-class-based-auth-views.
    """
    redirect_field_name = "target"

    def get(self, *args, **kwargs):
        alog.debug( 'starting shibboleth.views.ShibbolethLoginView.get()' )
        #Remove session value that is forcing Shibboleth reauthentication.
        self.request.session.pop(LOGOUT_SESSION_KEY, None)
        alog.debug( 'in shibboleth.views.ShibbolethLoginView.get(); settings.SHIB_MOCK_HEADERS, `%s`' % settings.SHIB_MOCK_HEADERS )
        if settings.SHIB_MOCK_HEADERS is True:
            redirect_url = self.request.GET.get( self.redirect_field_name )
        else:
            redirect_url = settings.LOGIN_URL + '?target=%s' % quote(self.request.GET.get(self.redirect_field_name))
        alog.debug( 'in shibboleth.views.ShibbolethLoginView.get(); redirect_url, `%s`' % redirect_url )
        return redirect( redirect_url )

    # def get(self, *args, **kwargs):
    #     #Remove session value that is forcing Shibboleth reauthentication.
    #     self.request.session.pop(LOGOUT_SESSION_KEY, None)
    #     login = settings.LOGIN_URL + '?target=%s' % quote(self.request.GET.get(self.redirect_field_name))
    #     return redirect(login)

class ShibbolethLogoutView(TemplateView):
    """
    Pass the user to the Shibboleth logout page.
    Some code borrowed from:
    https://github.com/stefanfoulis/django-class-based-auth-views.
    """
    redirect_field_name = "target"

    def get(self, *args, **kwargs):
        alog.debug( 'starting shibboleth.views.ShibbolethLogoutView.get()' )
        #Log the user out.
        auth.logout(self.request)
        #Set session key that middleware will use to force
        #Shibboleth reauthentication.
        self.request.session[LOGOUT_SESSION_KEY] = True
        #Get target url in order of preference.
        target = LOGOUT_REDIRECT_URL or\
                 quote(self.request.GET.get(self.redirect_field_name)) or\
                 quote(request.build_absolute_uri())
        logout = LOGOUT_URL % target
        alog.debug( 'in shibboleth.views.ShibbolethLogoutView.get(); redirect_url, `%s`' % logout )
        return redirect(logout)


