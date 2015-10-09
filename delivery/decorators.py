
import os

#===============================================================================
# Decorators for verifying user should be able to request items
#===============================================================================
from django.conf import settings
from django.http import HttpResponse
from django.template import loader, Context
from app_settings import SERVICE_CHECK_STRING

from middleware import make_denied_context



#logging
import logging
from django.conf import settings
from django.utils.log import dictConfig
dictConfig(settings.LOGGING)
alog = logging.getLogger('access')
alog.debug( 'test log entry' )



def has_service(func):
  """
  Decorator to ensure a logged in user can request items.
  """
  def decorator(request, *args, **kwargs):
    alog.debug( 'starting delivery.decorators.has_service()' )
    #Check to see if this is a dev environment.
    #If it is, return.
    if request.user.is_authenticated():
        if request.META.get('SERVER_NAME') in settings.DEV_SERVERS:
            pass
        else:
          shib = request.session.get('shib')
          if (not shib) or (SERVICE_CHECK_STRING not in shib.get('membership', '')):
              c = make_denied_context(request)
              return HttpResponse(c)
    return func(request, *args, **kwargs)
  return decorator

def has_email(func):
  """
  Decorator to ensure a logged in user has an email address.
  """
  def decorator(request, *args, **kwargs):
    alog.debug( 'starting delivery.decorators.has_email()' )
    if request.user.is_authenticated():
        email = request.user.email
        if (not email) or (email == ''):
            c = make_denied_context(request)
            return HttpResponse(c)
    return func(request, *args, **kwargs)
  return decorator
