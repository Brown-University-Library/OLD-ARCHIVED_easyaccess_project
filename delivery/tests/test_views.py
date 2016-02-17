
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
# from django.utils import unittest
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.client import Client
# from django.utils.importlib import import_module

from delivery import views



# class ConferenceReportResolverTest(TestCase):
#     def setUp(self):
#         self.factory = RequestFactory()
#     def test_econference_report(self):
#         request = self.factory.get('?id=10.1109/CCECE.2011.6030651')
#         response = views.ResolveView(request=request)
#         context = response.get_context_data()
#         citation = context['citation']
#         self.assertTrue('Electrical and Computer Engineering (CCECE), 2011 24th Canadian Conference on', citation['source'])
#         self.assertTrue('Islam', citation['creatorLast'])



# class ResolverTest(unittest.TestCase):
# class ResolverTest( TestCase ):
#     def setUp(self):
#         self.factory = RequestFactory()
#         #Settings for test client - http://stackoverflow.com/questions/4453764/how-do-i-modify-the-session-in-the-django-test-framework
#         settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
#         engine = import_module(settings.SESSION_ENGINE)
#         store = engine.SessionStore()
#         store.save()
#         self.session = store

#     def test_unicode(self):
#         """
#         No assertions.  Just make sure we are able to load the context.
#         """
#         q = u'?sid=FirstSearch:WorldCat&genre=book&isbn=9783835302334&title=Das "Orakel der Deisten" : Shaftesbury und die deutsche Aufklärung&date=2008&aulast=Dehrmann&aufirst=Mark-Georg&id=doi:&pid=<accession number>228805805</accession number><fssessid>0</fssessid>&url_ver=Z39.88-2004&rfr_id=info:sid/firstsearch.oclc.org:WorldCat&rft_val_fmt=info:ofi/fmt:kev:mtx:book&req_dat=<sessionid>0</sessionid>&rfe_dat=<accessionnumber>228805805</accessionnumber>&rft_id=info:oclcnum/228805805&rft_id=urn:ISBN:9783835302334&rft.aulast=Dehrmann&rft.aufirst=Mark-Georg&rft.btitle=Das "Orakel der Deisten" : Shaftesbury und die deutsche Aufklärung&rft.date=2008&rft.isbn=9783835302334&rft.place=Göttingen&rft.pub=Wallstein&rft.genre=book&rfe_dat=<dissnote>Thesis (doctoral)--Freie Universität, Berlin, 2006.</dissnote>'
#         request = self.factory.get(q)
#         request.session = self.session
#         response = views.ResolveView(request=request)
#         get = response.get(request)
#         context = response.get_context_data()

#         q = u'?rft.title=“iñtërnâtiônàlĭzætiøn”'
#         request = self.factory.get(q)
#         request.session = self.session
#         response = views.ResolveView(request=request)
#         get = response.get(request)
#         context = response.get_context_data()

#         self.assertEqual( 'a', 'b' )
