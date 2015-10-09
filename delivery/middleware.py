"""
Midleware that handles authentication for both the findit and delivery apps.
"""
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template import Context, loader
from django.conf import settings
from django.utils.log import dictConfig

from shibboleth.middleware import ShibbolethRemoteUserMiddleware
from shibboleth.middleware import ShibbolethValidationError
from models import LibraryProfile


import logging
dictConfig(settings.LOGGING)
alog = logging.getLogger('access')

class DeliveryShib(ShibbolethRemoteUserMiddleware):
    """
    Local subclass of django-shibboleth-remoteuser.

    Handles logging users in from Shib and creating their Django
    user profile.
    """

    def process_request(self, request):
        alog.debug( 'starting delivery.middleware.DeliveryShib.process_request()' )
        try:
            super(DeliveryShib, self).process_request(request)
        except (ImproperlyConfigured, ShibbolethValidationError, IntegrityError):
            #User can't be authenticated in these cases.
            #Store shib meta, logout, put shib meta back in session.
            shib = request.session.get('shib')
            logout(request)
            request.session['shib'] = shib
            c = make_denied_context(request)
            return HttpResponse(c, status=403)

    def make_profile(self, user, shib_meta):
        """
        A method is called on login.
        """
        alog.debug( 'starting delivery.middleware.DeliveryShib.make_profile()' )
        #Catch any occurrences where the profile doesn't yet exist.
        try:
            alog.debug( 'in delivery.middleware.DeliveryShib.make_profile(); type(user), `%s`' % type(user) )
            alog.debug( 'in delivery.middleware.DeliveryShib.make_profile(); user.__dict__, `%s`' % user.__dict__ )
            profile = user.libraryprofile
        except ObjectDoesNotExist:
            profile = LibraryProfile.objects.create(user=user)
        #Add extra information from Shib to complete profile.
        profile.barcode = shib_meta.get('barcode', None)
        affiliation = shib_meta.get('affiliation', None)
        if affiliation:
            for aff in affiliation.split(';'):
                aff = aff.lower().strip()
                if aff == 'faculty@brown.edu':
                    profile.is_faculty = True
                if aff == 'staff@brown.edu':
                    profile.is_staff = True
                if aff == 'student@brown.edu':
                    profile.is_student = True
        membership = shib_meta.get('membership', None)
        status = None
        if membership:
            for member in membership.split(';'):
                #BROWN:COMMUNITY:STUDENT:UNDERGRADUATE:ALL
                #BROWN:COMMUNITY:STUDENT:MEDICAL:ALL
                #BROWN:COMMUNITY:STUDENT:GRADUATE:ALL
                if member == 'BROWN:COMMUNITY:STUDENT:UNDERGRADUATE:ALL':
                    status = 'Undergraduate'
                    break
                elif member == 'BROWN:COMMUNITY:STUDENT:GRADUATE:ALL':
                    status = 'Graduate'
                    break
                elif member == 'BROWN:COMMUNITY:STUDENT:MEDICAL:ALL':
                    status = 'Medical Student'
                    break
                elif member == 'BROWN:COMMUNITY:EMPLOYEE:FACULTY:ALL':
                    status = 'Faculty'
                    break
        if status:
            profile.membership = status
        alog.debug("Shib profile: " + profile.membership)
        profile.save()
        user.save()


def make_denied_context(request):
    """
    Helper to prepare a template context when a user can't access a given
    page.

    Called here on exception and by decorators.
    """
    alog.info("%s was denied with membership: %s" % (request.user, request.session.get('shib')))
    t = loader.get_template('delivery/denied.html')
    c = Context({})
    c['back'] = request.META.get('HTTP_REFERER')
    c['ip'] = request.META.get('REMOTE_ADDR')
    if request.user.is_authenticated():
        c['email'] = request.user.email
    content = t.render(c)
    return content
