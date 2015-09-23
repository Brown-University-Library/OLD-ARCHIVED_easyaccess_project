"""
Test the bul_link views.  Note that a Serial Solutions API Key needs to be 
specified in settings.py for these to run.
"""

from django.conf import settings
from django.utils import unittest
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse

from pprint import pprint
import urlparse

from bul_link import views
from bul_link import models
from bul_link import urls

class ResolveViewTest(unittest.TestCase):
       
    def setUp(self):
        self.factory = RequestFactory()
        
    def test_resolved(self):
        """
        Check a known citation.
        """
        url = reverse('bul_link:resolve_view') + '/?pmid=21221393'
        request = self.factory.get(url)
        response = views.ResolveView(request=request)
        #Call get context data to simulate browser hit. 
        context = response.get_context_data()
        #Verify citation.
        citation = context['citation']
        self.assertEqual(citation['source'], 'Canadian family physician')
        self.assertEqual(citation['volume'], '38')
        self.assertEqual(citation['pmid'], '21221393')
        self.assertEqual('0008-350X', citation['issn']['print'])
        
    #To do: More tests for unresolved citations
        

class PermalinkTest(TestCase):
    fixtures = ['bul-link-test-data.json']
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_get_permalink(self):
        """
        Hit the permalink view and check the context for expected key,values.
        """
        url = reverse('bul_link:permalink_view', kwargs={'tiny': 'C'})
        request = self.factory.get(url)
        response = views.ResolveView(request=request)
        context = response.get_context_data(tiny='C')
        self.assertEqual(context['citation']['source'],
                         'The Journal of hand surgery, European volume')
        self.assertTrue(context['is_permalink'])
        #See if there is a link groups.  These will vary from site to site
        #so this will be a simple check. 
        self.assertTrue(context.has_key('link_groups'))
        
    def test_permalink_data(self):
        """
        Test data retrieved from the Resources database.
        """
        resource = models.Resource.objects.get(pk=1)
        self.assertTrue(resource.get_absolute_url().endswith('B/'))
        #Verify the query.
        qdict = urlparse.parse_qs(resource.query)
        self.assertEqual('APPL ENVIRON MICROB', qdict['rft.stitle'][0])
        self.assertEqual('Experimental examination of bacteriophage latent-period evolution as a response to bacterial availability',
                         qdict['rft.atitle'][0])
