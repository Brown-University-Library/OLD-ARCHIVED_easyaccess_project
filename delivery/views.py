# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, os, pprint, urlparse
from datetime import datetime

import bibjsontools, markdown, requests
from bibjsontools import from_dict, from_openurl, to_openurl
from decorators import has_email, has_service
from delivery import app_settings
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import redirect, render
from django.template import Context
from django.template import loader
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from py360link2 import get_sersol_data, Resolved
from shibboleth.decorators import login_optional
from utils import DeliveryBaseView, JSONResponseMixin, merge_bibjson, illiad_validate
# from delivery.classes.availability_helper import JosiahAvailabilityManager as AvailabilityChecker  # temp; want to leave existing references to `JosiahAvailabilityManager` in place for now
from delivery.classes.availability_helper import AvailabilityViewHelper
from delivery.classes.login_helper import LoginViewHelper
from delivery.classes.process_helper import ProcessViewHelper


log = logging.getLogger('access')
SERSOL_KEY = settings.BUL_LINK_SERSOL_KEY
# availability_checker = AvailabilityChecker()
availability_view_helper = AvailabilityViewHelper()
login_view_helper = LoginViewHelper()
process_view_helper = ProcessViewHelper()


def availability( request ):
    """ Manages borrow landing page where availability checks happen.
        Should get here after landing at 'find' urls, when item is a book. """
    querystring = request.META.get('QUERY_STRING', '').decode('utf-8')
    log.debug( 'starting; querystring, `{}`'.format(querystring) )
    log.debug( 'availability() request.session.items(), ```{}```'.format(pprint.pformat(request.session.items())) )

    ## check arrival
    valid = False
    if 'book' not in request.get_full_path():
        log.warning( 'why here since `book` not in request.full_path, ```{}```?'.format(request.get_full_path()) )
    if request.session.get( 'last_path', '' ) == '/easyaccess/find/':
        if request.session.get( 'last_querystring' ) == querystring:
            valid = True
    request.session['last_path'] = request.path
    if valid is False:
        redirect_url = '{findit}?{querystring}'.format(
            findit=reverse('findit:findit_base_resolver_url'), querystring=querystring )
        log.debug( 'redirect_url, ```{}```'.format(redirect_url) )
        return HttpResponseRedirect( redirect_url )

    ## get bib_dct
    bib_dct = availability_view_helper.build_bib_dct( querystring )

    ## get identifiers
    ( isbn, oclc_num ) = ( '', '' )
    for identifier in bib_dct['identifier']:
        if identifier['type'] == 'isbn':
            isbn = identifier['id']
        elif identifier['type'] == 'oclc':
            oclc_num = identifier['id']
    bib_dct['isbn'] = isbn
    bib_dct['oclc_num'] = oclc_num
    request.session['bib_dct_json'] = json.dumps(bib_dct)

    ## run recent request check -- TODO

    ## run josiah availability check
    isbn_url = '{ROOT}isbn/{ISBN}/'.format( ROOT=app_settings.AVAILABILITY_URL_ROOT, ISBN=isbn )
    log.debug( 'isbn_url, ```{}```'.format(isbn_url) )
    try:
        r = requests.get( isbn_url, timeout=7 )
        jdct = json.loads( r.content.decode('utf-8') )
    except Exception as e:
        log.error( 'Exception checking availability, ```{}```'.format(unicode(repr(e))) )
        jdct = {}
    log.debug( 'isbn-jdct, ```{}```'.format(pprint.pformat(jdct)) )
    # bib_num = jdct['id']
    available_holdings = []
    bib_num = jdct.get( 'id', None )
    if bib_num:
        isbn_holdings = []
        for item in jdct['items']:
            if item['is_available'] is True:
                isbn_holdings.append( {'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability']} )
        oclc_num_url = '{ROOT}oclc/{OCLC_NUM}/'.format( ROOT=app_settings.AVAILABILITY_URL_ROOT, OCLC_NUM=oclc_num )
        r = requests.get( oclc_num_url )
        jdct = json.loads( r.content.decode('utf-8') )
        log.debug( 'oclc_num-jdct, ```{}```'.format(pprint.pformat(jdct)) )
        oclc_holdings = []
        for item in jdct['items']:
            if item['is_available'] is True:
                oclc_num_callnumber = item['callnumber']
                # log.debug( 'oclc_num_callnumber, ```{}```'.format(oclc_num_callnumber) )
                match_check = False
                for holding in isbn_holdings:
                    log.debug( 'holding, ```{}```'.format(holding) )
                    if oclc_num_callnumber == holding['callnumber']:
                        match_check = True
                        break
                if match_check is False:
                    oclc_holdings.append( {'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability']} )
        for holding in oclc_holdings:
            isbn_holdings.append( holding )
        available_holdings = isbn_holdings

    # ## run josiah availability check
    # available_holdings = availability_view_helper.check_josiah_availability( isbn, oclc_num )

    ## set available flag
    available_locally = False
    if len( available_holdings ) > 0:
        available_locally = True

    ## if available, update db
    # if jam.available:
    #     jam.update_ezb_availability( bibj )

    ## build context
    ebook_dct = None
    ebook_json = request.session.get( 'ebook_json', None )
    log.debug( 'ebook_json, ```{}```'.format(ebook_json) )
    if ebook_json:
        ebook_dct = json.loads( ebook_json )
    permalink = request.session.get( 'permalink_url', '' )
    context = {
        'permalink_url': permalink,
        'bib': bib_dct,
        'exact_available_holdings': available_holdings,
        'available_locally': available_locally,
        'catalog_link': 'https://search.library.brown.edu/catalog/{}'.format( bib_num ),
        'report_problem_url': availability_view_helper.build_problem_report_url( permalink, request.META.get('REMOTE_ADDR', 'ip_not_available') ),
        'ebook_dct': ebook_dct,
        'ris_url': '{ris_url}?{eq}'.format( ris_url=reverse('findit:ris_url'), eq=querystring )
        }

    ## display landing page
    # resp = render( request, 'delivery/availability.html', context )
    if request.GET.get('output', '') == 'json':
        log.debug( 'will return json' )
        output = json.dumps( context, sort_keys=True, indent = 2 )
        resp = HttpResponse( output, content_type=u'application/javascript; charset=utf-8' )
    else:
        log.debug( 'will not return json' )
        resp = render( request, 'delivery/availability.html', context )
    return resp

    ## end def availability()


def login( request ):
    """ Forces shib-login, then
        (for now)
        - stores shib info to session
        - redirects user to process_request url/view
        (eventually)
        - gets or creates user-object and library-profile-data
        - redirects user to process_request url/view """

    ## check referrer
    ( referrer_ok, redirect_url ) = login_view_helper.check_referrer( request.session, request.META )
    if referrer_ok is not True:
        request.session['last_path'] = request.path
        return HttpResponseRedirect( redirect_url )
    request.session['last_path'] = request.path

    ## update bib_dct_json if needed
    easyborrow_volumes = request.POST.get( 'volumes', '' ).strip()
    if easyborrow_volumes != '':
        bib_dct = request.session.get( 'bib_dct_json', {} )
        bib_dct['easyborrow_volumes'] = easyborrow_volumes
        request.session['bib_dct_json'] = json.dumps( bib_dct )

    ## force login, by forcing a logout if needed
    ( localdev_check, redirect_check, shib_status ) = login_view_helper.assess_shib_redirect_need( request.session, request.get_host(), request.META )
    if redirect_check is True:
        ( redirect_url, updated_shib_status ) = login_view_helper.build_shib_redirect_url( shib_status=shib_status, scheme='https', host=request.get_host(), session_dct=request.session, meta_dct=request.META )
        request.session['shib_status'] = updated_shib_status
        log.debug( 'after assessing shib-redirect-need, redirecting to url, ```{}```'.format(redirect_url) )
        return HttpResponseRedirect( redirect_url )
    else:
        request.session['shib_status'] = ''  # makes assess_shib_redirect_need() trigger forced-login next time

    ## update user/profile objects
    # shib_dct = login_view_helper.update_user( localdev_check, request.META )  # will eventually return user object
    shib_dct = login_view_helper.update_user( localdev_check, request.META, request.get_host() )  # will eventually return user object
    request.session['user_json'] = json.dumps( shib_dct )

    ## redirect to process_request
    redirect_url = '{root_url}?{querystring}'.format( root_url=reverse('delivery:process_request_url'), querystring=request.session['last_querystring'] )
    return HttpResponseRedirect( redirect_url )


def process_request( request ):
    """ (for now)
        - Saves data to easyBorrow db
        - redirects user to message url/view
        (eventually)
        - Creates resource object, then
        - grabs user object
        - checks for recent request
        - saves data to easyBorrow db
        - redirects user to message url/view """

    ## check referrer
    ( referrer_ok, redirect_url ) = process_view_helper.check_referrer( request.session, request.META )
    request.session['last_path'] = request.path
    if referrer_ok is False:
        # request.session['message'] = 'Sorry, there was a problem with that url. easyBorrow requests should start _here_; contact us if this problem continues.'
        return HttpResponseRedirect( redirect_url )

    ## get/create resource object
    # resource_obj = process_view_helper.grab_resource( querystring )

    ## get user object
    # user_obj = process_view_helper.grab_user( request.META.get('Shibboleth-eppn', '') )

    ## check for recent request
    # if process_view_helper.check_recently_requested( user_obj, resource_obj ) is True:
    #     request.session['message'] = "You've recently requested this item and should soon receive an update email."
    #     return HttpResponseRedirect( reverse('delivery:message_url') )

    ## save new request
    # process_view_helper.save_request( user_obj, resource_obj )
    # process_view_helper.save_to_easyborrow( user_obj, resource_obj )
    shib_dct = json.loads( request.session.get('user_json', '{}') )
    bib_dct = json.loads( request.session.get('bib_dct_json', '{}') )
    ezb_db_id = process_view_helper.save_to_easyborrow( shib_dct, bib_dct, request.session.get('last_querystring', '') )

    ## evaluate result
    if ezb_db_id:
        # message = "Your request was successful; your easyBorrow transaction number is {}; you'll soon receive an update email.".format( ezb_db_id )
        message = process_view_helper.build_submitted_message( shib_dct['name_first'], shib_dct['name_last'], bib_dct, ezb_db_id, shib_dct['email'] )
    else:
        message = "There was a problem submitting your request, please try again in a few minutes, and if the problem persists, let us know via the feedback link."

    ## redirect to message url
    request.session['message'] = message
    return HttpResponseRedirect( reverse('delivery:message_url') )


def message( request ):
    """ Handles successful confirmation messages and problem messages. """
    context = {
        'last_path': request.session.get( 'last_path', '' ),
        'message': markdown.markdown( request.session.get('message', '') )
        }
    request.session['message'] = ''
    request.session['last_path'] = request.path
    return render( request, 'delivery/message.html', context )






# class ResolveView(DeliveryBaseView):
#     template_name = 'delivery/resolve.html'

#     @method_decorator(login_optional)
#     def dispatch(self, *args, **kwargs):
#         return super(ResolveView, self).dispatch(*args, **kwargs)

#     @property
#     def query(self):
#         #For handling unicode values in OpenURL
#         q = self.request.META.get('QUERY_STRING', None)
#         if not q:
#             try:
#                 q = self.openurl
#             except AttributeError:
#                 q = ''
#         return q

#     def get_gbs_identifier(self):
#         bib = self.bibj
#         if bib['type'] == 'book':
#             #try oclc
#             for id in bib.get('identifier', []):
#                 if id['type'] == 'oclc':
#                     return 'OCLC:%s' % id['id']
#                 elif id['type'] == 'isbn':
#                     return 'ISBN:%s' % id['id']
#         return

#     def pull_pmid(self, bib):
#         pmid = [k['id'].lstrip('info:pmid/') for k in bib.get('identifier', []) if k['type'] == 'pmid']
#         try:
#             return pmid[0]
#         except IndexError:
#             return

#     def pull_doi(self, bib):
#         doi = [k['id'].lstrip('doi:') for k in bib.get('identifier', []) if k['type'] == 'doi']
#         try:
#             return doi[0]
#         except IndexError:
#             return

#     def get(self, request, **kwargs):
#         # log.debug( 'bjd/in ResolveView.get()' )
#         log.debug( 'ResolveView.get() request.session.items(), ```%s```' % pprint.pformat(request.session.items()) )
#         import pubmed
#         from models import JosiahAvailabilityManager

#         #Check IP address and display message if user is using terminal.
#         if (self.request.META.get('REMOTE_ADDR') in settings.CLASSIC_IPS) and \
#             self.request.user.is_authenticated():
#             self.request.session['terminal'] = True
#         else:
#             self.request.session['terminal'] = False

#         #Return empty queries - this is the index page.
#         if (self.query == ''):
#             pass
#         else:
#             if self.request_dict:
#                 #check for pmid
#                 #pmid = self.pull_pmid()
#                 #if pmid:
#                 #    bibj = pubmed.to_bibjson(pmid)
#                 #else:
#                 bibj = from_dict(self.request_dict)
#             elif self.resource:
#                 bibj = from_openurl(self.resource.query)
#             else:
#                 raise Exception('Cant build a bibjson object.  Check ResolveView.get')
#             log.debug( 'in delivery.views.ResolveView.get(); bibj: %s' % pprint.pformat(bibj) )

#             #update ezb table if book & available
#             try:
#                 jam = JosiahAvailabilityManager()
#                 jam.check_josiah_availability( bibj )
#                 if jam.available:
#                     jam.update_ezb_availability( bibj )
#             except Exception as e:
#                 log.error( 'in delivery.views.ResolveView.get(); exception: %s' % unicode(repr(e)) )
#                 pass

#             #if there is a pubmed ID in the incoming request,
#             #send to the pubmed api for meta.
#             pmid = self.pull_pmid(bibj)
#             if pmid:
#                 bibj = pubmed.to_bibjson(pmid)

#             log.debug(bibj)
#             doi = self.pull_doi(bibj)
#             #Fill in metadta by pulling in data from 360link.
#             #We will skip any books coming from worldcat.
#             if (doi is not None) or (bibj.get('type') == 'inbook') or ('worldcat' not in bibj.get('_rfr', '').lower()):
#                 #This is a temporary work around to handle book chapters
#                 #with DOIs.
#                 try:
#                     pass
#                     #Get the openurl from the current bibjson object
#                     # ourl = to_openurl(bibj)
#                     # #Send this openurl to 360link for more metadata
#                     # data = new360link.link360.get(ourl, key=SERSOL_KEY, timeout=10)
#                     # sersol_bibj = data.json().get('records')[0]
#                     # log.debug('Sersol bibjson:')
#                     # log.debug(sersol_bibj)
#                     # bibj = merge_bibjson(bibj, sersol_bibj)
#                 except Exception, e:
#                     log.exception('Error querying 360Link for %s.' % doi)
#                 #log.debug('Adding values to validate ILLiad URL.')
#                 #bibj = illiad_validate(bibj)

#             bibj['_query'] = self.query
#             bibj['_has_fulltext'] = False
#             if bibj.get('link', None):
#                 bibj['_has_fulltext'] = True

#             self.bibj = bibj
#             self.cite = urlparse.parse_qs(self.query)

#         self.request.session['last_visited_resource'] = self.query
#         log.debug( 'in delivery.views.ResolveView.get(); about to return response' )
#         return super(ResolveView, self).get(request)

#     def get_context_data(self, **kwargs):
#         """
#         Prep the template view.
#         """
#         context = super(ResolveView, self).get_context_data(**kwargs)
#         context['terminal'] = self.request.session.get('terminal')
#         #handle index views.
#         if self.query == '':
#             self.template_name = 'delivery/index.html'
#             return context
#         context['openurl'] = self.bibj['_openurl']
#         context['bib'] = self.bibj
#         context['has_fulltext'] = self.bibj['_has_fulltext']
#         context['coin'] = self.bibj['_openurl']
#         context['cite_type'] = self.bibj['type']
#         context['cite'] = self.cite
#         context['query'] = self.query
#         context['bibjson'] = json.dumps(self.bibj)
#         if settings.DEBUG:
#             from utils import make_illiad_url
#             context['illiad'] = make_illiad_url(self.bibj)
#         #book covers
#         context['gbs'] = self.get_gbs_identifier()
#         #confirmation for requests
#         tn = kwargs.get('transaction_number', '0')
#         context['confirmation'] = tn
#         log.debug( 'in delivery.views.ResolveView.get(); context, ```{}```'.format(pprint.pformat(context)) )
#         return context

class Link360View(DeliveryBaseView):
    default_json = True
    PRINT_DB_NAME = 'Brown Print Journal Holdings'

    def pull_print(self, issns, start, end):
        """
        Get the print title information and return Django query object.
        """
        from findit.models import PrintTitle
        if (start == '') or (end == ''):
            return []
        #Normalize start and end - dates are 2007-01-01.
        start = int(start.split('-')[0])
        try:
            end = int(end.split('-')[0])
        except IndexError:
            #set this for open ended dates.
            end = 4000
        print_set = PrintTitle.objects.filter(issn__in=issns,
                                                     start__lte=start,
                                                     end__gte=end)
        return print_set

    def bibjson(self, citation, format):

        bib = {}
        #Handle type
        if format == 'book':
            bib['type'] = 'book'
        elif format == 'journal':
            #see if there is a title, then it is an article
            if citation.get('title', None) is not None:
                bib['type'] = 'article'
            else:
                bib['type'] = 'journal'
        else:
            bib['type'] = 'misc'

        #journal names
        if bib['type'] != 'book':
            bib['journal'] = {'name': citation.get('source')}

        #pages
        bib['start_page'] = citation.get('spage')

        #title and author are the same for all fromats in bibjson
        bib['title'] = citation.get('title')
        author = [
                         {'name': citation.get('creator'),
                          'firstname': citation.get('creatorFirst'),
                          'lastname': citation.get('creatorLast')
                          }
                         ]
        #ToDo: Pull out empty keys for authors
        bib['author'] = author
        bib['year'] = citation.get('date', '-').split('-')[0]
        bib['issue'] = citation.get('issue')
        bib['volume'] = citation.get('volume')
        bib['publisher'] = citation.get('publisher')
        bib['address'] = citation.get('publicationPlace')


        #Get potential identifiers
        ids = [{
                'type': 'doi',
                'id': citation.get('doi')
                },
                {
                'type': 'issn',
                'id': citation.get('issn', {}).get('print')
                },
               {
                'type': 'eissn',
                'id': citation.get('eissn')
                },
               {
                'type': 'pmid',
                'id': citation.get('pmid')
        }]
        ids = filter(lambda id: id['id'] is not None, ids)
        #add isbns to identifiers
        isbns = citation.get('isbn', [])
        for isbn in isbns:
            ids.append({'type': 'isbn',
                        'id': isbn})
        bib['identifier'] = ids

        return bib

    def get_print(self, bibjson, link_groups):
        out = []
        for grp in link_groups:
            db = grp['holdingData']['databaseName']
            #check for print
            if db == self.PRINT_DB_NAME:
                issns = [i['id'] for i in bibjson['identifier'] if i['type'] == 'issn']
                start = bibjson['year']
                for pheld in self.pull_print(issns, start, start):
                    _h = {}
                    _h['location'] = pheld.location
                    _h['callnumber'] = pheld.call_number
                    avail = 'Check shelf'
                    if pheld.location == 'Annex':
                        avail = 'By request'
                    _h['availability'] = avail
                    _h['request_link'] = 'http://josiah.brown.edu/search/c%s' % pheld.call_number
                    #We don't want to display duplicate locations and call numbers
                    if _h not in out:
                        out.append(_h)
        return out



    def make_links(self, groups):
        """
        Process the link groups.
        """

        def _best(grp):
            """
            Get the best link for each link group.
            """
            out = {}
            db = grp['holdingData']['databaseName']
            if db == self.PRINT_DB_NAME:
                return

            #direct
            dl = grp['url'].get('article')
            book = grp['url'].get('book')
            issue = grp['url'].get('issue')
            journal = grp['url'].get('journal')
            out['anchor'] = db
            if dl:
                out['url'] = dl
                out['type'] = 'direct'
            elif book:
                out['url'] = book
                out['type'] = 'direct'
            #issue
            elif issue:
                out['url'] = issue
                out['type'] = 'issue'
            elif journal:
                out['url'] = journal
                out['type'] = 'journal'
            else:
                return
            return out

        #Get the best links available.
        link_sets = [l for l in map(_best, groups) if l]
        #Get direct links only by removing anything without type direct.
        #This needs to
        try:
            direct = filter(lambda x: x.get('type', 'na') == 'direct', link_sets)
        except AttributeError:
            direct = []
        #Return direct links if we've got them.
        if len(direct) > 0:
            return {'direct': direct}
        else:
            return {'other': link_sets}
        #pull out links we won't display


    def get_context_data(self, **kwargs):
        """
        Hit the 360 Link API and return the data as json.
        """
        #output dict
        d = {}
        query = self.request.META.get('QUERY_STRING', None)
        data = get_sersol_data(query, key=SERSOL_KEY, timeout=25)
        #d['raw'] = data
        try:
            results = data['results'][0]
            links = self.make_links(results['linkGroups'])
            d['links'] = links
            meta = data['echoedQuery']
            d['bibjson'] = self.bibjson(results['citation'], results['format'])
            print_held = self.get_print(d['bibjson'], results['linkGroups'])
            d['print'] = print_held
            d.update(meta)
            d.update(results)
        except IndexError:
            pass
        #parsed_query = urlparse.parse_qs(query)
        #d['raw_qs'] = parsed_query
        return d


# class RequestView(ResolveView):
#     template_name = 'delivery/resolve.html'
#     default_json = False

#     @method_decorator(has_email)
#     @method_decorator(has_service)
#     def dispatch(self, *args, **kwargs):
#         return super(RequestView, self).dispatch(*args, **kwargs)

#     def create_request(self, bib):
#         from models import Request
#         request = Request()
#         request.user = self.request.user
#         request.bib = bib
#         request.save(submit=True)
#         return request.transaction_number

#     def get_resource(self, bib):
#         from models import Resource
#         #Get or create a resource for the given query.  Catch cases where
#         #there are duplicate queries in the resource db.  Shouldn't happen
#         #but is during testing.
#         try:
#             resource, created = Resource.objects.get_or_create(query=bib['_query'])
#         except MultipleObjectsReturned:
#             resource = Resource.objects.filter(query=bib['_query'])[0]
#             created = False
#         if created:
#             resource.referrer = bib.get('_rfr', 'unknown')
#             resource.save()
#         return (resource, created)


#     def post(self, *args, **kwargs):
#         from django.shortcuts import redirect
#         posted = self.request.POST
#         resource = None
#         #Create a bibjson object from what we know.
#         #See if we have a posted bib
#         if 'bib' in posted:
#             bib_str = posted.get('bib')
#             bib = json.loads(bib_str)
#             resource, created = self.get_resource(bib)
#         else:
#             #If no posted bib, we are going to pull it from the session
#             resource = self.request.session.get('requested_item', None)
#             if resource:
#                 bib  = from_openurl(resource.query)
#             else:
#                 raise Exception('Expecting request in session')
#             bib  = from_openurl(resource.query)
#             bib['_query'] = resource.query

#         #If user is not yet authenticated, pass them to the login url.
#         if not self.request.user.is_authenticated():
#             #route_to_login
#             return redirect(self.login_url(resource))
#         #see if user is allowed to request materials
#         elif (self.request.user.is_authenticated()) and\
#             (self.request.session.get('not_authorized')):
#             #render the denied template
#             t = loader.get_template('delivery/denied.html')
#             c = Context({})
#             return HttpResponse(t.render(c))
#         else:
#             #Handle the request now.
#             transaction_number = self.create_request(bib)
#             self.request.session['transaction_number'] = transaction_number
#             self.request.session['requested_item'] = resource
#             return redirect(resource.get_absolute_url())

#     def get(self, request, **kwargs):
#         """
#         Users can get to the RequestView from a GET request in some cases.
#             - direct links/hits to a borrow/request url.
#             - redirects from Shibboleth

#         If the user is logged in, we will check the session for a request and
#         process it.

#         If the user is not logged in, we will set a warning message to the
#         session and then redirect them to login.  They can then procced.
#         """
#         #Get the resource by looking up the permalink from the kwargs
#         resource = self.request.session.get('requested_item', None)
#         #Try to get the resource from the URL.
#         if resource is None:
#             plink = kwargs.get('tiny', None)
#             if not plink:
#                 #There is something odd here.
#                 #This is GET request to the request view
#                 #and no request-able item is in the session.
#                 #We will try to return the user to the last visited resource.
#                 #If we can't, we will display an error message where they
#                 #can leave us feedback about what happened.
#                 log.warning("User %s accessed request page via GET and no request in session." % self.request.user)
#                 last_query = self.request.session.get('last_visited_resource', None)
#                 if (last_query is not None) and (last_query != ''):
#                     return HttpResponseRedirect('./?%s' % last_query)
#                 else:
#                     log.warning("No resource or last visited resource found.  User accessed request view without a plink in kwargs or request in session.")
#                     t = loader.get_template('delivery/denied.html')
#                     c = Context({})
#                     return HttpResponse(t.render(c))
#             resource = self.get_resource_from_plink(plink)

#         #If the user is authenticated, try to process the request.
#         if self.request.user.is_authenticated():
#             #Check to see if this request was passed from from Shibboleth
#             #Is this a redirect after login with a request in the session?
#             #Is this user being redirected from Shib?
#             http_origin = self.request.META.get('HTTP_ORIGIN', 'unknown')
#             from_shib = http_origin.rfind('sso.brown.edu') > -1
#             #If the user has HTTP origin from Shib or the last login is with two
#             #seconds, process the request.
#             last_login_delta = (datetime.now() - self.request.user.last_login).seconds
#             if (from_shib) or (last_login_delta) < 10:
#                 query = resource.query
#                 bib  = from_openurl(query)
#                 bib['_query'] = query
#                 #Delete the resource from the session to prevent duplicate requests.
#                 try:
#                     del self.request.session['requested_item']
#                 except KeyError:
#                     pass
#                 #Make the request
#                 transaction_number = self.create_request(bib)
#                 self.request.session['transaction_number'] = transaction_number

#             else:
#                 log.warning("User %s accessed requst page via GET and no request in session." % self.request.user)
#                 self.request.session['attempted_request_message'] = \
#                                      "Were you trying to request this item?  Something went wrong.\
#                                      Please click \"Request this item\" again."
#         return redirect(resource.get_absolute_url())

# class PermalinkView(ResolveView):

#     def get(self, request, **kwargs):
#         """Process the request."""
#         from models import Resource
#         from shorturls.baseconv import base62
#         from bibjsontools import ris
#         plink = kwargs.get('tiny', None)
#         resource = self.get_resource_from_plink(plink)
#         #Set this for the query helper utility
#         self.openurl = resource.query
#         self.resource = resource
#         #Check for export param
#         export = self.request.GET.get('export', 'none')
#         if export == 'ris':
#             import string
#             #For stripping punctuation for the download filename.
#             exclude = set(string.punctuation)
#             #export to RIS if requested
#             bib = from_openurl(resource.query)
#             title = bib.get('title', 'bul')
#             slug = ''.join(ch for ch in title if ch not in exclude)
#             filename = slug.replace(' ', '-').lower()
#             rtext = ris.convert(bib)
#             response = HttpResponse(rtext,
#                                     content_type='application/x-research-info-systems')
#             response['Content-Disposition'] = 'attachment; filename=%s.ris' % filename
#             return response
#         return super(PermalinkView, self).get(request)

#     def post(self, *args, **kwargs):
#         from models import Resource
#         out = {}
#         posted = self.request.POST
#         bib = json.loads(posted['bib'])
#         #import pdb; pdb.set_trace()
#         #Get or create a resource for the given query.
#         try:
#             resource, created = Resource.objects.get_or_create(query=bib['_openurl'])
#         except MultipleObjectsReturned:
#             resource = Resource.objects.filter(query=bib['_openurl'])[0]
#             created = False
#         resource.referrer = bib.get('_rfr', 'unknown')
#         resource.save()
#         out['permalink'] = resource.get_absolute_url()
#         out['ip'] = self.request.META.get('REMOTE_ADDR')
#         #If the user is logged in, return their email address to for adding to the
#         #problem report form.
#         if self.request.user.is_authenticated():
#             out['email'] = self.request.user.email

#         return HttpResponse(json.dumps(out),
#                             mimetype='application/json')


#     def get_context_data(self, **kwargs):
#         context = super(PermalinkView, self).get_context_data(**kwargs)
#         #Make lower case true because this will be interpreted as javascript
#         context['permalink'] = 'true'
#         #A user might some how link to a request permalink.  In these cases\
#         #render the attempted request message from the session.
#         attempted_request = self.request.session.get('attempted_request_message', None)
#         if attempted_request is not None:
#             context['attempted_request'] = attempted_request
#             self.request.session['attempted_request_message'] = None

#         #See if this is a requested item. If it is, render the transaction number
#         #and delete it from the session.
#         tn = self.request.session.get('transaction_number', None)
#         if tn:
#             context['transaction_number'] = tn
#             del self.request.session['transaction_number']
#             #Delete the request from the session to prevent duplicate requests.
#             try:
#                 del self.request.session['requested_item']
#             except KeyError:
#                 pass
#         return context

# class UserInfoView(ResolveView):
#     default_json = True

#     @method_decorator(login_required)
#     def dispatch(self, *args, **kwargs):
#         return super(UserInfoView, self).dispatch(*args, **kwargs)

#     def get_context_data(self, **kwargs):
#         from models import Request
#         from datetime import datetime, timedelta
#         context = {}
#         context['query'] = self.query
#         context['requested'] = False
#         try:
#             profile = self.request.user.libraryprofile
#         except ObjectDoesNotExist:
#             #In odd cases a user won't have a profile.
#             return context
#         context['primary_affiliation'] = profile.primary_affiliation()
#         context['can_request_print'] = profile.can_request_print()
#         if self.query != '':
#             #There really should only be one - but we will code it as a list
#             #in case we want to leave open the possiblity of several request.
#             #See if the user has requested this item within the last month.
#             check_date = datetime.today() - timedelta(minutes=15)
#             user_requests = Request.objects.filter(user=self.request.user,
#                                                    date_created__gte=check_date,
#                                                    item__query=self.query).order_by('-date_created')
#             context['requests'] = [{'transaction_number': e.transaction_number,
#                                     'date': e.date_created.strftime('%m-%d-%Y'),
#                                     'time': e.date_created.strftime('%H:%M %p'),
#                                     'seconds_ago': (datetime.now() - e.date_created).seconds,
#                                     }\
#                                    for e in user_requests]
#             if len(context['requests']) > 0:
#                 context['requested'] = True
#         return context


# class ProcessBibView(ResolveView):
#     """
#     Take bibjson objects from a POST and process by returning an openurl or some
#     other resource fetching.
#     """
#     default_json = True
#     def post(self, *args, **kwargs):
#         from utils import make_illiad_url
#         out = {}
#         posted = self.request.POST
#         #import pdb; pdb.set_trace()
#         bib = json.loads(posted['bib'])
#         out['bib'] = bib
#         openurl = to_openurl(bib)
#         out['bib']['_openurl'] = openurl
#         out['illiad_url'] = make_illiad_url(bib)
#         out['coin'] = openurl
#         return HttpResponse(json.dumps(out),
#                             mimetype='application/json')


#     def get_context_data(self, **kwargs):
#         context = super(ProcessBibView, self).get_context_data(**kwargs)
#         #Make lower case true because this will be interpreted as javascript
#         #context['openurl'] = to_openurl(context['bib'])
#         #context['illiad'] = self.make_illiad_url(context['bib'])
#         return context

class StaffView(DeliveryBaseView):
    template_name = 'delivery/staff.html'

    def make_data(self):
        from models import Request
        req = Request.objects.all()
        requests = [
            {
             u"label": r.id,
             u"type": u"Request",
             u"transaction_number": r.transaction_number,
             u"permalink": r.item.get_absolute_url(),
             u"title": r.bib['title'],
             u"date": r.date_created.isoformat(),
             u"by": "%s %s" % (r.user.first_name, r.user.last_name),
             u"openurl": r.bib['_query'],
             u"rfr": r.bib['_rfr'],
             }
            for r in req
        ]
        return requests

    def get(self, request, **kwargs):
        if self.request.GET.get('exhibit', None) == 'true':
            requests = self.make_data()
            #do the queries.
            #requests within last 10 days.
            exhibit_obj = {
                           'types': {
                                     'Request': {
                                                'pluralLabel': "Requests"
                                                }
                                     },
                           'items': requests
                           }
            return HttpResponse(json.dumps(exhibit_obj),
                            mimetype='application/json')
        else:
            return super(StaffView, self).get(request)

