# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
import json


#===============================================================================
# Merge bibjson oobjects.
# Code from https://github.com/okfn/bibserver/blob/bibwiki/bibserver/dao.py
#===============================================================================
def merge_bibjson(a, b) :
    def _merge(a, b):
        #https://github.com/okfn/bibserver/blob/bibwiki/bibserver/dao.py
        for k, v in a.items():
            if k.startswith('_') and k not in ['_collection']:
                pass
            if isinstance(v, dict) and k in b:
                merge_bibjson(v, b[k])
            elif isinstance(v, list) and k in b:
                if not isinstance(b[k], list):
                    b[k] = [b[k]]
                for idx, item in enumerate(v):
                    if isinstance(item,dict) and idx < len(b[k]):
                        merge_bibjson(v[idx],b[k][idx])
                    elif item not in b[k]:
                        b[k].append(item)
        a.update(b)
        return a

    out = _merge(a, b)
    return out

#===============================================================================
# For Illiad work.
#===============================================================================
def make_illiad_url(bibjson):
    """
    Create an Illiad request URL from bibsjon.  Requires adding a couple of
    Illiad specific fields.
    """
    import urllib
    import urlparse
    from app_settings import ILLIAD_URL
    from bibjsontools import to_openurl
    base = ILLIAD_URL
    #Send to validate_bib to add default values missing fields.
    bib = illiad_validate(bibjson)
    #Holder for values to add to the raw openurl
    extra = {}
    #Get OCLC or pubmed IDS
    identifiers = bibjson.get('identifier', [])
    for idt in identifiers:
        if idt['type'] == 'pmid':
            extra['Notes'] = "PMID: %s.\r via easyAccess" % idt['id']
        elif idt['type'] == 'oclc':
            extra['ESPNumber'] = idt['id']
    if bib.get('_valid') is not True:
        if extra.get('Notes') is None:
            extra['Notes'] = ''
        extra['Notes'] += "\rNot enough data provided by original request."
    ourl = to_openurl(bib)
    for k,v in extra.iteritems():
        ourl += "&%s=%s" % (urllib.quote_plus(k), urllib.quote_plus(v))
    illiad = base % ourl
    return illiad

def illiad_validate(bib):
    """
    Validates a bibjson objects for Illiad.
    It simply adds default values for required fields that are
    missing.
    """
    valid = True
    if bib['type'] == 'article':
        if bib.get('journal') is None:
            d = {'name': 'Not provided'}
            bib['journal'] = d
            valid = False
        if bib.get('year') is None:
            bib['year'] = '?'
            valid = False
        if bib.get('title') is None:
            bib['title'] = "Title not specified"
            valid = False
        if bib.get('pages') is None:
            bib['pages'] = '? - ?'
            valid = False
    elif bib['type'] == 'book':
        if bib.get('title') is None:
            bib['title'] = 'Not available'
            valid = False
    #These should all be inbooks but checking for now.
    elif (bib['type'] == 'bookitem') or (bib['type'] == 'inbook'):
        if bib.get('title') is None:
            bib['title'] = "Title not specified"
            valid = False
        if bib.get('journal') is None:
            d = {'name': 'Source not provided'}
            bib['journal'] = d
            valid = False
        pages = bib.get('pages')
        if (pages == []) or (pages is None):
            bib['pages'] = '? - ?'
            valid = False
    bib['_valid'] = valid
    return bib

#===============================================================================
# Base views for the delivery app.  Others will inherit from these.
#===============================================================================
from django.views.generic import TemplateView
from django.http import HttpResponse
class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        params = self.request.GET
        if params.has_key('callback'):
            content = "%s(%s)" % (params['callback'], content)
        return HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: this needs to be better to ensure that you are seralizing what
        # is needed as JSON.  For now just popping known problems.
        #Also see - https://docs.djangoproject.com/en/dev/topics/serialization/
        remove = ['user', 'resource', 'profile']
        for rem in remove:
            try:
                del context[rem]
            except KeyError:
                pass
        return json.dumps(context)

#Login optional mixin
from django.utils.decorators import method_decorator
#shibboleth helpers
from shibboleth.decorators import login_optional
class LoginOptionalMixin(object):
    u"""Will log the user in if Shib attributes found."""

    @method_decorator(login_optional)
    def dispatch(self, *args, **kwargs):
        return super(LoginOptionalMixin, self).dispatch(*args, **kwargs)


class PublicTerminalMixin(object):
    """
    Mixin to display the logout warning if a user is using a
    public terminal.
    """

    def get_context_data(self, **kwargs):
        """
        Prep the template view.
        """
        #Check IP address and display message if user is using terminal.
        if (self.request.META.get('REMOTE_ADDR') in settings.CLASSIC_IPS) and \
            self.request.user.is_authenticated():
            term = True
        else:
            term = False
        ctx = super(PublicTerminalMixin, self).get_context_data(**kwargs)
        ctx['terminal'] = term
        return ctx


class DeliveryBaseView(PublicTerminalMixin, TemplateView, LoginOptionalMixin, JSONResponseMixin):
    template_name = 'delivery/index.html'
    default_json = False

    @property
    def query(self):
        return self.request.META.get('QUERY_STRING', None)

    @property
    def request_dict(self):
        return dict(self.request.GET)

    def is_dev_server(self):
        """
        Helper to see if we are using the dev server.
        """
        if settings.DEBUG:
            server = self.request.META.get('wsgi.file_wrapper', None)
            if server is not None and server.__module__ == 'django.core.servers.basehttp':
                return True
        return False

    def login_url(self, resource):
        """
        Helper for Shib logins.
        """
        redirect_field_name = 'target'
        if self.is_dev_server():
            redirect_field_name = 'next'
        url = "%s?%s=%s" % (
                              settings.LOGIN_URL,
                              redirect_field_name,
                              resource.get_absolute_url(request_view=True))
        return url

    def get_resource_from_plink(self, short):
        from models import Resource
        from shorturls.baseconv import base62
        from django.core.exceptions import MultipleObjectsReturned
        resource_id = base62.to_decimal(short)
        try:
            resource = Resource.objects.get(id=resource_id)
        except MultipleObjectsReturned:
            resource = Resource.objects.filter(id=resource_id)[0]
        return resource

    def render_to_response(self, context):
        # Look for a 'output=json' GET argument
        if (self.request.GET.get('output','html') == 'json')\
            or (self.default_json):
            return JSONResponseMixin.render_to_response(self, context)
        else:
            return super(DeliveryBaseView, self).render_to_response(context)

