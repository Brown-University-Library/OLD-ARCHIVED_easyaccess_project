# -*- coding: utf-8 -*-

from __future__ import unicode_literals
"""
Views for the resolver.
"""
#django stuff
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render, render_to_response
from django.core.urlresolvers import reverse, get_script_prefix
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.log import dictConfig
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache

#stdlib
import json
import urllib2
import re

#installed packages
# from bul_link.baseconv import base62
# from bul_link.views import BulLinkBase, ResolveView
from bul_link.views import BulLinkBase
# from bul_link.models import Resource
from py360link2 import Link360Exception

#local
from models import Request, UserMessage
import forms
# from utils import BulSerSol, make_illiad_url, Ourl, get_cache_key
from utils import BulSerSol, FinditResolver, Ourl
from utils import get_cache_key, make_illiad_url
from app_settings import BOOK_RESOLVER, ILLIAD_REMOTE_AUTH_URL,\
                         ILLIAD_REMOTE_AUTH_HEADER, EMAIL_FROM,\
                         MAS_KEY, PROBLEM_URL, SUMMON_ID, SUMMON_KEY,\
                         SERVICE_ACTIVE, EXTRAS_TIMEOUT, SERVICE_OFFLINE

import summon

try:
    from easy_article.delivery.decorators import has_email, has_service
    from easy_article.delivery.utils import PublicTerminalMixin
except ImportError:
    from delivery.decorators import has_email, has_service
    from delivery.utils import PublicTerminalMixin

#One week.
EXTRAS_CACHE_TIMEOUT = 604800 #60*60*24*7

#check for non-standard pubmed queries.
PMID_QUERY = re.compile('^pmid\:(\d+)')

fresolver = FinditResolver()


#logging
import logging
dictConfig(settings.LOGGING)
ilog = logging.getLogger('illiad')
alog = logging.getLogger('access')



def base_resolver( request ):
    """ Handles link resolution. """
    alog.debug( 'starting; query_string, `%s`' % request.META.get('QUERY_STRING', 'no-query-string') )
    referrer = fresolver.get_referrer( request.GET ).lower()
    if fresolver.check_summon( referrer ):
        if fresolver.enhance_link( request.GET.get('direct', None), request.META.get('QUERY_STRING', None) ):
            return HttpResponseRedirect( fresolver.enhanced_link )
    if fresolver.check_sersol_publication( request.GET, request.META.get('QUERY_STRING', None) ):
        return HttpResponseRedirect( fresolver.sersol_publication_link )
    context = { 'login_link': 'foo' }
    return render( request, 'findit/index.html', context )




def redirect_to_sersol(query):
    """
    Simple view for re-routing to serial solutions.
    """
    return HttpResponseRedirect(
                                'http://%s.search.serialssolutions.com/?%s' % (
                                                                      settings.BUL_LINK_SERSOL_KEY,
                                                                      query)
    )

class Resolver(PublicTerminalMixin, BulLinkBase):
    template_name = 'findit/resolve.html'
    default_json = False
    is_permalink = False

    def get_permalink(self):
        tiny = base62.from_decimal(self.resource.id)
        return reverse('findit:permalink-view', kwargs={'tiny': tiny})

    def get_base_url(self):
        app_prefix = get_script_prefix()
        return ''.join(('http', ('', 's')[self.request.is_secure()], '://', self.request.META['HTTP_HOST']))

    def make_ris(self):
        """
        Export citation as RIS.
        """
        from export import ris
        format = self.resolved.format
        citation = self.resolved.citation
        ris = ris(citation, format)
        response = HttpResponse(ris,
                                content_type='application/x-research-info-systems')
        response['Content-Disposition'] = 'attachment; filename=easyArticle-%s.ris' % self.resource.id
        return response

    def get_referrer(self):
        """
        Get the referring site and append to links headed elsewhere.  Helpful for
        tracking down ILL request sources.  This should really be in a separate
        OpenURL parsing utility but was having trouble pulling it out given the
        existing flow.  This ensures that it gets added to the OpenURL
        that is generated from 360Link data.
        """
        sid = None
        ea='easyArticle'
        qdict = self.request.GET
        sid = qdict.get('sid', None)
        #Try rfr_id if not found in sid.
        if not sid:
            sid = qdict.get('rfr_id', None)
        if sid:
            return "%s-%s" % (sid, ea)
        else:
            return ea

    def get(self, request, **kwargs):
        """Process the request."""
        alog.debug( 'starting findit.views.Resolver.get()' )
        if SERVICE_ACTIVE is False:
            return redirect_to_sersol(self.query)

        if SERVICE_OFFLINE is True:
            self.template_name = 'findit/service_offline.html'
            sersol = None
            self.resolved = None

        #Let's see if we have a PMID or a DOI and if so
        #fetch a link from Summon for those.
        rfr = self.get_referrer().lower()
        #Skip Summon lookup for certain providers.
        check_summon = True
        for provider in settings.FINDIT_SKIP_SUMMON_DIRECT_LINK:
            if rfr.find(provider) > 0:
                check_summon = False
                break
        if check_summon is True:
            alog.debug( 'starting findit.views.Resolver.get(); check_summon is True' )
            #Make sure the GET request doesn't override this.
            if self.request.GET.get('direct') == 'false':
                pass
            else:
                alog.debug( 'starting findit.views.Resolver.get(); enhanced_link will be built' )
                enhanced_link = summon.get_enhanced_link(self.query)
                #TODO - use the metadata from Summon to render the request
                #page rather than hitting the 360Link API for something
                #that is known not to be held.
                if enhanced_link:
                    alog.info("Summon link found for %s -- %s." % (self.query,
                                                                   enhanced_link))
                    return HttpResponseRedirect(enhanced_link)
        #Check to see if this is a request for an individual publication
        qdict = self.request.GET
        #Pass publication requests on to 360link for now.
        if qdict.get('rft.genre', 'null') == 'journal':
            if qdict.get('sid', 'null').startswith('FirstSearch'):
                issn = qdict.get('rft.issn')
                return redirect_to_sersol(self.query)

        o = Ourl(self.query)
        o.make_cite()
        ourl_cite = o.cite
        plink = kwargs.get('tiny', None)
        if plink:
            #Convert incoming permalink to database pk.
            rid = base62.to_decimal(plink)
            try:
                resource = Resource.objects.get(id=rid)
            except MultipleObjectsReturned:
                resource = Resource.objects.filter(query=bib['_query'])[0]
            self.resource = resource
            sersol = self.get_data(query=resource.query)
            self.is_permalink = True
        elif not self.query:
            self.template_name = 'findit/index.html'
            sersol = None
            self.resolved = None
        #route pmid request through Summon.
#        elif (ourl_cite.get('pmid', None)) and\
#             (qdict.get('output', None) != 'json'):
#            pmid = ourl_cite.get('pmid')
#            u = reverse('findit:summon-view', kwargs={'id_type': 'pmid',
#                                                      'id_value': pmid})
#            u += '?%s' % self.query
#            return redirect(u)
        else:
            #Catch  non-standard pubmed queries.
            pmid_match = re.match(PMID_QUERY, self.query)
            if pmid_match:
                pmid = pmid_match.group(1)
                new_query = 'pmid=%s' % pmid
                #This could create the same problems as normal pubmed queries
                #but we are going to try for now.
                sersol = self.get_data(query=new_query)
            else:
                sersol = self.get_data()
        #import pdb; pdb.set_trace()
        if sersol is not None:
            #Create a resolved object
            try:
                self.resolved = BulSerSol(sersol)
            except Link360Exception:
                cite_url = "%s?%s" % (reverse('findit:citation-form-view'),
                                      self.query)
                return redirect(cite_url)
            #It's no longer necessary to treat Summon links differently.
            #The search display is using the index enhanced links.
            #Send Summon referrals with direct link to the link.  E.g. one click.
            # try:
            #     rfr_id = ourl_cite.get('rfr_id', '')
            #     if (rfr_id.rindex('summon.serialssolutions') > -1)\
            #         and (qdict.get('output', None) != 'json'):
            #         dl = self.resolved.access_points()['direct_link']
            #         if not dl:
            #             pass
            #         else:
            #             link = dl.get('link', None)
            #             if link:
            #                 return HttpResponseRedirect(link)
            # except ValueError:
            #     pass
            #If it's a book and no electronic access is available, send to easyBorrow.
            if BOOK_RESOLVER is not None:
                #don't redirect JSON requests.
                if self.request.GET.get('output', None) == 'json':
                    pass
                #check for books with article level electronic links
                elif self.resolved.access_points()['resolved']:
                    pass
                else:
                    if (self.resolved.format == 'book') or (self.resolved.format == 'unknown'):
                        #pass original query
                        ourl = self.query or self.resource.query
                        return HttpResponseRedirect(BOOK_RESOLVER % ourl)

        #Check to see if this is a request for an export format.
        if self.is_permalink is True:
            #Check to see if there is export param for citation formats
            export = self.request.GET.get('export', None)
            if export:
                if self.request.GET['export'] == 'ris':
                    return self.make_ris()
        else:
            #6/27/13 - Work around for problem with ISSN 0022-0949 where
            #the 360Link knowledgebase has it assigned to two separate
            #journals.  Prof. Sharon Swartz has reported this several times.
            #For some reason, the default interface is able to handle these but
            #not the API.  I have a support request into Sersol for resolution.
            try:
                if (self.request.GET.get('output', None) != 'json') and ('0022-0949' in self.resolved.citation.get('issn').values()):
                    publisher_link = 'http://revproxy.brown.edu/login?url=http://jeb.biologists.org/search?submit=yes&submit=Submit&pubdate_year={0}&volume={1}&firstpage={2}'
                    #http://jeb.biologists.org/search?submit=yes&submit=Submit&pubdate_year=1996&volume=199&firstpage=609
                    doi = self.resolved.citation.get('doi')
                    volume = self.resolved.citation.get('volume')
                    year = self.resolved.citation.get('date')[0:4]
                    first = self.resolved.citation.get('spage')
                    if doi is not None:
                        return HttpResponseRedirect('http://revproxy.brown.edu/login?url=http://dx.doi.org/' + doi)
                    elif (volume is not None) and (year is not None) and (first is not None):
                        return HttpResponseRedirect(publisher_link.format(year, volume, first))
                    #send to native interface for now.
                    #return redirect_to_sersol(self.query.replace('sid=google', ''))
            except AttributeError:
                pass

        #return HttpResponseRedirect('http://{{ SS_KEY }}.search.serialssolutions.com/?%s' % self.query)
        alog.debug( 'leaving findit.views.Resolver.get()' )
        return super(Resolver, self).get(request)
        ## end of def Resolver.get() ##

    def get_context_data(self, **kwargs):
        """
        Prep the template view.
        """
        context = super(Resolver, self).get_context_data(**kwargs)
        #This is the home page
        if self.resolved == None:
            return context
        #Always using the first citation and linkGroups returned.  It's not
        #clear when multiple citations would be useful.
        citation = self.resolved.citation
        context['link_groups'] = self.resolved.link_groups
        context['resource'] = self.resource
        context['format'] = self.resolved.format
        context['direct_link'] = self.resolved.access_points()['direct_link']
        #if citation.get('title', '') == '':
        #    citation['title'] = "
        context['citation'] = citation
        #add the access points
        context.update(self.resolved.access_points())
        openurl = self.resolved.openurl
        context['openurl'] = openurl
        context['coin'] = openurl.replace('url_ver', 'ctx_ver')
        ourl_referrer = self.get_referrer()
        illiad_params =  make_illiad_url(context['openurl'])
        illiad_base = 'https://illiad.brown.edu/illiad/illiad.dll/OpenURL'
        context['illiad_url'] = '%s?%s&sid=%s' % (illiad_base, illiad_params, ourl_referrer)
        context['permalink'] = self.get_permalink()
        #Add the permanent link and IP to the problem report url.
        # print 'PROBLEM_URL, `%s`' % PROBLEM_URL
        problem_url = PROBLEM_URL % (self.get_base_url().rstrip('/') + context['permalink'],
                                    self.request.META.get('REMOTE_ADDR', 'unknown'))
        # print 'problem_url, `%s`' % problem_url
        context['problem_link'] = problem_url
        context['is_permalink'] = self.is_permalink
        context['login_url'] = settings.LOGIN_URL
        #Google Scholar search link
        gscholar_base = getattr(settings, 'FINDIT_GSCHOLAR')
        if gscholar_base:
            #Get meta to put into gscholar search
            if (citation.get('title')) and (citation.get('creatorLast')):
                context['gscholar'] = gscholar_base % (citation)
        #For displaying request links
        if self.request.user.is_authenticated():
            #This should only trigger an exception on the development server.
            try:
                profile = self.request.user.libraryprofile
                context['profile'] = profile
                #Can request print - medical or faculty
                context['can_request_print'] = profile.can_request_print()
            except ObjectDoesNotExist:
                context['profile'] = None
        else:
            context['profile'] = None
            #prompt for login if we have print materials and the user is not authenticated.
            if len(context['print']) > 0:
                context['prompt_login'] = True

        context['login_link'] = 'foo'

        return context


class SummonView(BulLinkBase):
    template_name = 'findit/summon.html'
    default_json = False

    def get_base_url(self):
        app_prefix = get_script_prefix()
        return ''.join(('http', ('', 's')[self.request.is_secure()], '://', self.request.META['HTTP_HOST']))

    def make_ris(self):
        """
        Export citation as RIS.
        """
        from export import ris
        citation = self.summon_citation['citation']
        ris = ris(citation, 'journal')
        response = HttpResponse(ris,
                                content_type='application/x-research-info-systems')
        response['Content-Disposition'] = 'attachment; filename=easyArticle.ris'
        return response

    def get_permalink(self):
        summon_path = reverse('findit:summon-view', kwargs={'id_type': 'pmid',
                                                            'id_value': self.pmid})
        return '%s%s' % (self.get_base_url(), summon_path)

    def get(self, request, **kwargs):
        import urllib
        api_id = os.environ['EZACS__SUMMON_API_ID']
        api_key = os.environ['EZACS__SUMMON_API_KEY']
        ident = kwargs.get('id_type')
        pmid = kwargs.get('id_value')
        cite_url = "%s?%s" % (reverse('findit:citation-form-view'), 'pmid:%s' % pmid)
        self.pmid = pmid
        #Fetch from summ
        q = 's.q=' + urllib.quote_plus('PMID:"%s"' % pmid)
        sum = summon.SummonSearch(SUMMON_ID, SUMMON_KEY)
        resp = sum.fetch(q)
        sum = summon.SummonResponse(resp)
        docs = sum.docs()
        if len(docs) == 0:
            return HttpResponseRedirect(cite_url)
        self.summon_citation = summon.summon_citation(docs[0])
        self.echoedQuery = sum.echoedQuery

        #Check to see if there is export param for citation formats
        export = self.request.GET.get('export', None)
        if export:
            if self.request.GET['export'] == 'ris':
                return self.make_ris()

        return super(SummonView, self).get(request)


    def get_context_data(self, **kwargs):
        """
        Process the returned Summon document.
        """
        context = super(SummonView, self).get_context_data(**kwargs)
        sersol = self.summon_citation
        sersol['echoedQuery'] = self.echoedQuery
        context.update(sersol)
        context['pmid'] = self.pmid
        openurl = sersol['openurl']
        #Raw openurl and coin
        context['openurl'] = openurl + '&pmid=' + self.pmid
        context['coin'] = context['openurl'].replace('url_ver', 'ctx_ver')
        #Template is expecting this
        context['direct_link'] = ''
        #Handle pemalinks and problem reports.
        plink = self.get_permalink()
        #Add the permanent link and IP to the problem report url.
        problem_url = PROBLEM_URL % (self.get_base_url().rstrip('/') + plink,
                                    self.request.META.get('REMOTE_ADDR', 'unknown'))
        context['problem_link'] = problem_url
        context['permalink'] = plink
        context['is_permalink'] = True
        #Make a resource entry for this request.
        scrubbed_query = self.scrub_query()
        context['resource'] = self.make_resource(scrubbed_query)
        return context


class CitationFormView(BulLinkBase):
    template_name = 'findit/citation_linker.html'
    default_json = False

    def get_permalink(self):
        tiny = base62.from_decimal(self.resource.id)
        return reverse('findit:permalink-view', kwargs={'tiny': tiny})

    def make_form_from_query(self, qdict):
        """
        Take an un-resolveable OpenURL and attempt to pull out metadata
        that can pre-populate a citation linker form.

        We could potentially hit the Worldcat API to get more metadata for those
        OpenURLs passed on from worldcat.org.
        """
        #import pdb; pdb.set_trace()
        citation_form_dict = {}
        for k,v in qdict.items():
            if (v) and (v != ''):
                v = v[0]
                if k == 'id':
                    if v.startswith('doi'):
                        k = 'doi'
                        v = v.replace('doi:', '')
                #for oclc numbers
                v = v.replace('<accessionnumber>', '')\
                     .replace('</accessionnumber>', '')
                citation_form_dict[k] = v
        d = {}
        d['article_form'] = forms.ArticleForm(citation_form_dict)
        d['book_form'] = forms.BookForm(citation_form_dict)
        #d['dissertation_form'] = forms.DissertationForm(citation_form_dict)
        #d['patent_form'] = forms.PatentForm(citation_form_dict)
        return d

    def get_base_url(self):
        app_prefix = get_script_prefix()
        return ''.join(('http', ('', 's')[self.request.is_secure()], '://', self.request.META['HTTP_HOST']))


    def get_context_data(self, **kwargs):
        import urlparse
        context = super(CitationFormView, self).get_context_data(**kwargs)
        query = self.request.META.get('QUERY_STRING', None)
        #Catch non standard pubmed queries
        pmid_match = re.match(PMID_QUERY, self.query)
        if pmid_match:
            pmid = pmid_match.group(1)
            query = 'pmid=%s' % pmid
        cforms = {
             'article_form': forms.ArticleForm(),
             'book_form': forms.BookForm(),
             #'dissertation_form': forms.DissertationForm(),
             #'patent_form': forms.PatentForm()
             }
        if not query:
            #Default to article form
            context['form_type'] = 'article'
        else:
            try:
                sersol = self.get_data(query=query)
                resolved = BulSerSol(sersol)
                #prep a completed form
                cforms = resolved.get_citation_form()
                context['format'] = resolved.format
                context['citation'] = resolved.citation
                context['direct_link'] = ''
                if resolved.is_requestable() == False:
                    context['linker_message'] = "Please add more information about the resource: article title, journal title, date and page range are required."
            except Link360Exception:
                context['linker_message'] = "There was not enough information provided\
                to complete your request.  Please add more information about the\
                resource.  A Journal, ISSN, DOI, or PMID is required."
                #Attempt to massage incoming request into something that can
                #prepopulate the form.
                qdict = urlparse.parse_qs(query)
                if qdict.get('rft.genre', [''])[0] == 'book':
                    context['form_type'] = 'book'
                else:
                    context['form_type'] = 'article'
                cforms = self.make_form_from_query(qdict)
        context.update(cforms)
        context['login_url'] = settings.LOGIN_URL
        context['openurl'] = self.query
        #Add the permanent link and IP to the problem report url.
        try:
            plink = self.get_permalink()
        except AttributeError:
            plink = '/citation-form/'
        problem_url = PROBLEM_URL % (self.get_base_url().rstrip('/') + plink,
                                    self.request.META.get('REMOTE_ADDR', 'unknown'))
        context['problem_link'] = problem_url
        return context


class RequestView(PublicTerminalMixin, BulLinkBase):
    template_name = 'findit/request.html'
    default_json = False
    #@method_decorator(login_required)

    alog.debug( 'in findit.views.RequestView; about to run has_email decorator' )
    @method_decorator(has_email)
    @method_decorator(has_service)
    def dispatch(self, *args, **kwargs):
        alog.debug( 'starting findit.views.RequestView.dispatch()' )
        return super(RequestView, self).dispatch(*args, **kwargs)

    def send_message(self, message_type, **kwargs):
        addr = self.request.user.email
        message = UserMessage.objects.get(type=message_type)
        message_from = EMAIL_FROM
        if message_type == 'confirmation':
            request_object = kwargs.get('request', None)
            #full_path = ''.join(full_path)
            illiad_request_url = settings.FINDIT_ILLIAD_URL.replace('OpenURL?%s', '') + '?Action=10&Form=63&Value=%s' % request_object.illiad_tn

            msg = message.text.replace('{{ILLIAD_TN}}', request_object.illiad_tn)
            msg = msg.replace('{{ILLIAD_TRANS_URL}}', illiad_request_url)

            body = "%s" % (msg)
        elif message_type == 'blocked':
            resource = kwargs.get('resource', None)
            rid = resource.id
            tiny = base62.from_decimal(rid)
            plink = reverse('findit:permalink-view', kwargs={'tiny': tiny})
            full_path = ('http', ('', 's')[self.request.is_secure()], '://', self.request.META['HTTP_HOST'], plink)
            full_path = ''.join(full_path)
            body = "%s\n%s" % (message.text, full_path)
        else:
            body = message.text
        #sendit
        send_mail(message.subject,
                  body,
                  message_from,
                  [addr],
                  fail_silently=True)


    def get(self, request, *args, **kwargs):
        """
        Handle the request.  Ensure enough metadata is available for requesting.
        """
        resource_id = kwargs.get('resource', None)
        #Handle users not already authenticated.
        if not self.request.user.is_authenticated():
            url = "%s?target=%s" % (
                                  settings.LOGIN_URL,
                                  reverse('findit:request-view', kwargs={'resource': resource_id}))
            return redirect(url)

        ilog.info('User %s is at request page %s.' % (self.request.user.id,
                                                  resource_id))
        resource = Resource.objects.get(id=resource_id)
        #Check to see if the user has requested the given resource.
        try:
            requested = Request.objects.filter(item=resource_id,
                                               user=self.request.user)
            self.existing_request = requested[0]
        except IndexError:
            self.existing_request = None
        sersol = self.get_data(resource.query)
        self.resolved = BulSerSol(sersol)
        self.item = resource
        #Make sure we have enough metadata.  If we don't, send it along to the
        #citation linker.  In some cases a DOI won't return a page number
        #but will have a direct link.  We don't want to display the citation
        #link in that case.
        #if not self.resolved.access_points()['resolved']:
        #   if self.resolved.is_requestable() == False:
        #       cite_url = "%s?%s" % (reverse('findit:citation-form-view'),
        #                             resource.query)
        #       return redirect(cite_url)



        #Illiad testing.
#        from illiad.account import IlliadSession
#        profile = self.request.user.libraryprofile
#        illiad_profile = profile.illiad()
#        ill_username = illiad_profile['username']
#        illiad = IlliadSession(ILLIAD_REMOTE_AUTH_URL,
#                               ILLIAD_REMOTE_AUTH_HEADER,
#                               ill_username)
#        illiad_session = illiad.login()
#        ilog.info('User %s established Illiad session: %s.' % (ill_username,
#                                                              illiad_session['session_id']))
#        illiad.registered = False
#        if not illiad_session['authenticated']:
#            out['session_error'] = 'Failed login.'
#            ilog.error("Illiad login failed for %s" % ill_username)
#        else:
#            #Register users if neccessary.
#            if not illiad.registered:
#                ilog.info('Will register %s with illiad.' % (ill_username))
#                ilog.info('Registering %s with Illiad as %s.' % (ill_username,
#                                                                 illiad_profile['status'])
#                          )
#                reg = illiad.register_user(illiad_profile)
#                ilog.info('%s registration response: %s' % (ill_username, reg))
#        #end testing block

        return super(RequestView, self).get(request)

    @method_decorator(login_required)
    def post(self, *args, **kwargs):
        from illiad.account import IlliadSession
        posted = self.request.POST
        resource = Resource.objects.get(id=posted['resource'])
        #Mock what the JS is expecting.
        out = {}
        #For development - requests aren't sent to ILLiad.
        if self.request.META.get('SERVER_NAME') in settings.DEV_SERVERS:
            out['submit_status'] = {'submitted': True, 'id': 1234}
            out['blocked'] = False
            out['session'] = {'authenticated': True}
            req = Request.objects.create(
                                        item=resource,
                                        user=self.request.user,
                                        illiad_tn='new'
            )
            req.save()
            return HttpResponse(json.dumps(out),
                               mimetype='application/json')
        profile = self.request.user.libraryprofile
        illiad_profile = profile.illiad()
        ill_username = illiad_profile['username']
        #Get the OpenURL we will submit.
        ill_url = posted['ill_openurl']
        ilog.info('User %s posted %s for request.' % (ill_username,
                                                       ill_url))
        out = {}
        #Get an illiad instance
        illiad = IlliadSession(ILLIAD_REMOTE_AUTH_URL,
                               ILLIAD_REMOTE_AUTH_HEADER,
                               ill_username)
        illiad_session = illiad.login()
        ilog.info('User %s established Illiad session: %s.' % (ill_username,
                                                              illiad_session['session_id']))
        out['session'] = illiad_session

        if not illiad_session['authenticated']:
            out['session_error'] = 'Failed login.'
            ilog.error("Illiad login failed for %s" % ill_username)
        else:
            #Register users if neccessary.
            if not illiad.registered:
                ilog.info('Will register %s with illiad.' % (ill_username))
                ilog.info('Registering %s with Illiad as %s.' % (ill_username,
                                                                 illiad_profile['status'])
                          )
                reg = illiad.register_user(illiad_profile)
                ilog.info('%s registration response: %s' % (ill_username, reg))

            illiad_post_key = illiad.get_request_key(ill_url)
            #If blocked comes back in the post key, stop here with appropriate status.
            blocked = illiad_post_key.get('blocked', None)
            errors = illiad_post_key.get('errors', None)
            if blocked:
                out['blocked'] = blocked
                ilog.info("%s is blocked in Illiad." % ill_username)
                self.send_message('blocked', resource=resource)
            elif errors:
                out['errors'] = True
                msg = illiad_post_key['message']
                ilog.info("Request errors during Illiad submission: %s %s" %\
                            (ill_username,
                             self.msg))
                out['message'] = msg
            else:
                #Submit this
                #out['submit_key'] = illiad_post_key
                submit_status = illiad.make_request(illiad_post_key)
                #Mock a request for testing.
#                submit_status = {
#                               'transaction_number': '1234',
#                               'submitted': True,
#                               'error': False,
#                               'message': None
#                               }
                out['submit_status'] = submit_status
                #Write the request to the requests table.
                if submit_status['submitted']:
                    illiad_tn = submit_status['transaction_number']
                    req = Request.objects.create(item=resource,
                                                 user=self.request.user,
                                                 illiad_tn=illiad_tn)
                    self.send_message('confirmation', request=req)
                    ilog.info("%s request submitted for %s with transaction %s." %\
                            (ill_username,
                             req.id,
                             illiad_tn))
                else:
                    ilog.error("%s request failed with message %s." %\
                               (ill_username,
                               submit_status['message']))
        illiad.logout()
        return HttpResponse(json.dumps(out),
                            mimetype='application/json')


    def get_context_data(self, **kwargs):
        context = super(RequestView, self).get_context_data(**kwargs)
        #Get the article id, if not raise an error.
        #These are client side requests to see if the authenticated user has already requested the item.
        #Check to see if this user has requested this item already.
#        lookup = self.request.GET.get('lookup', None)
#        if (lookup) and (self.request.user):
#            self.default_json = True
#            try:
#                item_request = Request.objects.get(item=perma_key,
#                                          user=self.request.user)
#                out = {}
#                out['requested'] = True
#                out['date'] = item_request.date_created.isoformat()
#                return out
#            except ObjectDoesNotExist:
#                out = {}
#                out['requested'] = False
#                return out
        #hit the resolver
        citation = self.resolved.citation
        context['format'] = self.resolved.format
        context['citation'] = self.resolved.citation
        context['resource'] = self.resource
        context['openurl'] = self.resolved.openurl
        #Build the openurl from the citation metadata plus the original referrer.
        context['ill_openurl'] = "%s&sid=%s" % (make_illiad_url(context['openurl']), self.item.referrer)
        context['illiad_url'] = 'https://illiad.brown.edu/illiad/illiad.dll/OpenURL?' + context['ill_openurl']
        context['existing_request'] = self.existing_request
        ilog.info('Illiad url to be submitted: %s' % context['illiad_url'])
        return context


class UserView(BulLinkBase):
    """
    This is mainly just here to offer a Shib protected page that we can
    route users through to login.
    """
    template_name = 'findit/user_info.html'
    default_json = False

    #Django docs say to decorate the dispatch method for
    #class based views.
    #https://docs.djangoproject.com/en/dev/topics/auth/
    #@method_decorator(login_required)
    #@login_required
    def dispatch(self, *args, **kwargs):
        return super(UserView, self).dispatch(*args, **kwargs)

    def check_redirect(self):
        n = self.request.GET.get('next', None)
        t = self.request.GET.get('target', None)
        target = n if n is not None else t
        #import ipdb; ipdb.set_trace()
        return target

    def get(self, request, **kwargs):
        """Process the request."""
        rd = self.check_redirect()
        if rd is not None:
            return redirect(rd)
        return super(UserView, self).get(request)

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        #if a cite get paramaeter, then redirect
        rd = self.check_redirect()
        if rd:
            #hacky but good enough for now.
            context['redirect'] = rd
        return context


class MicrosoftView(BulLinkBase):
    default_json = True

    def get_context_data(self, **kwargs):
        import urllib
        #One week.
        EXTRAS_CACHE_TIMEOUT = 604800 #60*60*24*7
        query = self.request.GET
        base = 'http://academic.research.microsoft.com/json.svc/search'
        p = {}
        #check for key
        if not MAS_KEY:
            p['query'] = query
            p['error'] = 'No MAS_API key supplied'
            return p

        p['AppId'] = MAS_KEY
        au = query.get('rft.au', None)
        if au:
            p['AuthorQuery'] = au.encode('utf-8', 'ignore')
        ti = query.get('rft.atitle', None)
        if ti:
            p['TitleQuery'] = ti.encode('utf-8', 'ignore')
        date = query.get('rft.date')
        if date:
            p['YearQuery'] = date.encode('utf-8', 'ignore')

        #static
        p['PublicationContent'] = 'title,author,doi,abstract,fullversionurl,journal'
        p['StartIdx'] = '1'
        p['EndIdx'] = '1'


        query = urllib.urlencode(p)

        api_url = "%s?%s" % (base, query)
        out = {}
        out['cached'] = False
        #Pull the results from the cache or pull from the API.
        ck = 'mas%s' % query.replace(' ', '')
        ck = get_cache_key(ck)
        #data = cache.get(ck, None)
        #if data:
        #    out['cached'] = True
        #else:
        try:
            data = json.load(urllib2.urlopen(api_url, timeout=EXTRAS_TIMEOUT))['d']
            cache.set(ck, data, EXTRAS_CACHE_TIMEOUT)
        #Should explicitly check for some errors.  Getting 500 errors.
        except:
            data = 'error'
        out['response'] = data
        #Echo results but pop api key from params
        del p['AppId']
        out['query'] = urllib.urlencode(p)
        return out


class JstorView(BulLinkBase):
    default_json = True
    ns = {'srw': 'http://www.loc.gov/zing/srw/',
           'jstor': 'http://dfr.jstor.org/sru/elements/1.1'}

    def x(self, doc, pth):
        spot = doc.xpath('./srw:recordData[1]/jstor:%s' % pth, namespaces=self.ns)
        #empty elements
        if len(spot) == 0:
            return
        elif len(spot) == 1:
            return spot[0].text
        else:
            return [e.text for e in spot]
        #return doc.xpath('./srw:recordData[1]/jstor:%s[1]/text()' % pth, namespaces=ns)[0]

    def stable(self, doc):
        jid = self.x(doc, 'id')
        jurl_id = self.id(doc)
        base = 'http://www.jstor.org/stable/%s'
        return base % jurl_id

    def id(self, doc):
        jid = self.x(doc, 'id')
        jurl_id = jid.replace('10.2307/', '')
        return jurl_id

    def format(self, doc):
        """
        Normalize format to book or article.
        """
        jtype = self.x(doc, 'resourcetype')
        if jtype == 'book-review':
            return 'book'
        else:
            return 'article'

    def title(self, doc):
        t = self.x(doc, 'title')
        if type(t) == str:
            return t
        else:
            return ' '.join([e for e in t])

    def pull_results(self, query):
        import urllib
        from lxml import etree
        base = 'http://dfr.jstor.org/sru'
        params = {}
        params['version'] = '1.1'
        params['operation'] = 'searchRetrieve'
        params['recordSchema'] = 'info:srw/schema/srw_jstor'
        params['maximumRecords'] = 15
        params['recordPacking'] = 'xml'
        params['operation'] = 'searchRetrieve'
        params['query'] = query


        query = urllib.urlencode(params)
        u = "%s/?%s" % (base, query)
        try:
            f = urllib2.urlopen(u, timeout=EXTRAS_TIMEOUT)
            doc = etree.parse(f)
        except IOError:
            alog.info("JSTOR timeout for %s" % query)
            doc = None
            results = []

        if doc:
            """
            {
            doi: "10.1109/MHS.2004.1421324",
            isbn: [
            "9780780386075",
            "9780780386075"
            ],
            creator: "Ronkanen, P.",
            creatorLast: "Ronkanen",
            source: "Proceedings of the 2004 International Symposium on Micro-NanoMechatronics and Human Science : the Fourth Symposium "Micro-NanoMechatronics for an Information-Based Society" : the 21st Century COE Program, Nagoya University : Nagoya Municipal Industrial Res",
            creatorFirst: "P.",
            date: "2004",
            title: "Self heating of piezoelectric actuators: measurement and compensation",
            spage: "1"
            },

            """

            recs = doc.xpath('srw:records[1]/srw:record', namespaces=self.ns)

            #for r in recs:
            #    print x(r, 'jstor:resourcetype')
            proxy_prefix = 'http://revproxy.brown.edu/login?url='
            results = [
                {
                 #'type': x(r, 'resourcetype'),
                 'title': self.title(r),
                 'source': self.x(r, 'journaltitle'),
                 'discipline': self.x(r, 'discipline'),
                 'doi': self.x(r, 'id'),
                 'stable': '%s%s' % (proxy_prefix, self.stable(r)),
                 'format': self.format(r),
                 'topics': self.x(r, 'topics'),
                 'pages': self.x(r, 'pagerange'),
                 'issn': self.x(r, 'issn'),
                 'volume': self.x(r, 'volume'),
                 'issue': self.x(r, 'issue'),
                 'author': self.x(r, 'author'),
                 'abstract': self.x(r, 'abstract'),
                 'id': self.id(r),
                 #http://www.jstor.org/stable/info/2781822?seq=1&type=ref#infoRef
                 #http://www.jstor.org/stable/info/2781822?seq=1&type=cite#infoCiting
                 'references': '%shttp://www.jstor.org/stable/info/%s?seq=1&type=ref#infoRef' % (proxy_prefix, self.id(r)),
                 'citations': '%shttp://www.jstor.org/stable/info/%s?seq=1&type=cite#infoCiting' % (proxy_prefix, self.id(r)),
                 'pdf': '%shttp://www.jstor.org/stable/pdfplus/%s.pdf' % (proxy_prefix, self.id(r)),
                }
                for r in recs
            ]
        out = {}
        out['results'] = results
        out['source_url'] = u
        return out

    #@method_decorator(cache_control(must_revalidate=False, max_age=3600))
    def dispatch(self, *args, **kwargs):
        return super(JstorView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        import urlparse
        import urllib
        #One week.
        EXTRAS_CACHE_TIMEOUT = 604800 #60*60*24*7
        qdict = urlparse.parse_qs(self.request.META['QUERY_STRING'])
        #Build sru query string
        query = ''
        author = qdict.get('rft.aulast', None)
        qchunks = []
        if author:
            qchunks.append('dc.creator="%s"' % author[0])
        title = qdict.get('rft.atitle', None)
        if title:
            #we don't want sub titles which generally appear after :
            t = title[0].split(':')[0]
            qchunks.append('dc.title="%s"' % t)
        source = qdict.get('rft.jtitle', None)
        if source:
            qchunks.append('jstor.journaltitle="%s"' % source[0])
        sru_query =  ' and '.join(qchunks)
        out = {}
        #Default response
        out['results'] = []
        out['cached'] = False
        #Only send queries if we have sufficient metadat.
        if author:
            if title:
                if source:
                    alog.info("JSTOR query string: %s" % sru_query)
                    #Cache here.
                    ck = 'jstor%s' % sru_query.replace(' ', '')
                    ck = get_cache_key(ck)
                    res = cache.get(ck, None)
                    if res is None:
                        res = self.pull_results(sru_query)
                        cache.set(ck, res, EXTRAS_CACHE_TIMEOUT)
                    else:
                        out['cached'] = True
                    out.update(res)
        out['qdict'] = qdict
        out['query'] = sru_query
        return out

def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context: None
    """
    from django.shortcuts import render_to_response
    from django.template import RequestContext
    template_name = 'findit/500.html'
    return render_to_response(template_name,
        context_instance = RequestContext(request)
    )

def not_found_error(request, template_name='404.html'):
    """
    404 error handler.

    Templates: `404.html`
    Context: None
    """
    from django.shortcuts import render_to_response
    from django.template import RequestContext
    template_name = 'findit/404.html'
    return render_to_response(template_name,
        context_instance = RequestContext(request)
    )


