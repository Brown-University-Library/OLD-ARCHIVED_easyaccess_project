from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.core.urlresolvers import get_script_prefix
from django.core.exceptions import MultipleObjectsReturned

#standard lib
import base64
import json
import urllib
import urlparse
#3rd party
from lxml import etree

#local
from baseconv import base62
from py360link import get_sersol_data, Resolved

from models import Resource

from app_settings import SERSOL_KEY, CACHE_TIMEOUT, QUERY_SKIP_KEYS, SERSOL_TIMEOUT

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

class BulLinkBase(TemplateView, JSONResponseMixin):
    
    def get_base_url(self):
        app_prefix = get_script_prefix()
        return ''.join(('http', ('', 's')[self.request.is_secure()], '://', self.request.META['HTTP_HOST']))
    
    def get_context_data(self, **kwargs):
        context = super(BulLinkBase, self).get_context_data(**kwargs)
        context['direct_link'] = None
        return context
    
    def get_referrer(self):
        """
        Get the referring site if possible.  Will be stored in the database. 
        """
        sid = None
        try:
            qdict = self.resource.query
        except AttributeError:
            qdict = urlparse.parse_qs(self.scrub_query())
        sid = qdict.get('sid', None)
        #Try rfr_id if not found in sid.
        if not sid:
            sid = qdict.get('rfr_id', None)
        if not sid:
            oclc = qdict.get('pid', None)
            if (oclc) and ('accession number' in oclc):
                sid = 'OCLC'
        if sid:
            return "%s-%s" % (sid, ea) 
        else:
            return 'easyArticle-unknown'
    
    def get_data(self,
                 query=None,
                 cache_timeout=CACHE_TIMEOUT):
        """
        Get and process the data from the API and store in Python dictionary.
        This data is where any caching should take place.  
        """
        #See if this view has created a resource already.
        try:
            query = self.resource.query
        except:
            #If no query is passed in, use the self.scrubbed_query property
            if query is None:
                query = self.scrub_query()
            #Get or make resource
            resource = self.make_resource(query)
            self.resource = resource
            
        cache_key = "resolved-%s" % self.resource.id
        data = cache.get(cache_key, None)
        if not data:
            data = get_sersol_data(query, key=SERSOL_KEY, timeout=SERSOL_TIMEOUT)
            cache.set(cache_key, data, cache_timeout)
        return data
    
    def make_resource(self, scrubbed_query):
        """
        Try to find the requested resource in the local database.  If it doesn't
        exist.  A permalink will be created on save.
        """
        try:
            resource, created = Resource.objects.get_or_create(query=scrubbed_query)
        except MultipleObjectsReturned:
            resource = Resource.objects.filter(query=scrubbed_query)[0]
            created = False
        resource.referrer = self.get_referrer()
        resource.save()
        #Add logger message here.
        return resource
        

    def render_to_response(self, context):
        # Look for a 'output=json' GET argument  
        if (self.request.GET.get('output','html') == 'json')\
            or (self.default_json):
            return JSONResponseMixin.render_to_response(self, context)
        else:
            return super(BulLinkBase, self).render_to_response(context)
        
    @property
    def query(self):
        return self.request.META.get('QUERY_STRING', None)
    
    def scrub_query(self):
        """
        Scrub the original query request.  This normalizes the
        order of the keys and removes keys that aren't needed to resolve the
        citation.
        
        Dictionary sorting from:
        http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
        http://code.activestate.com/recipes/52306-to-sort-a-dictionary/
        """
        query = self.query
        skip_keys = QUERY_SKIP_KEYS
        parsed = urlparse.parse_qs(query)
        #Pull out the keys we don't want.  Skip any blank keys.  
        new = sorted([(k, v) for k,v in parsed.items() \
                      if v != ''\
                      if k not in skip_keys],
                     key=lambda x: x[1])
        #as string
        qs = urllib.urlencode(new, doseq=True)
        return qs
    
class ResolveView(BulLinkBase):
    template_name = 'bul_link/resolve.html'
    default_json = False
    
    def get_context_data(self, **kwargs):
        context = super(ResolveView, self).get_context_data(**kwargs)
        #Check for permalink view.
        plink = kwargs.get('tiny', None)
        if plink:
            #Convert incoming permalink to database pk.  
            rid = base62.to_decimal(plink)
            #Get resource from cache if possible.
            cache_key = "resource-%s" % rid
            resource = cache.get(cache_key, None)
            if resource is None:
                resource = Resource.objects.get(id=rid)
                cache.set(cache_key, resource, CACHE_TIMEOUT)
            self.resource = resource
            sersol = self.get_data(query=resource.query)
            context['is_permalink'] = True
        #Show index screen
        elif not self.query:
            self.template_name = 'bul_link/index.html'
            return context
        #Resolve the query
        else:
            sersol = self.get_data()
        
        resolved = Resolved(sersol)
        #Always using the first citation and linkGroups returned.  It's not
        #clear when multiple citations would be useful.
        context['citation'] = resolved.citation
        context['link_groups'] = resolved.link_groups
        context['resource'] = self.resource
        return context
    

    
    

