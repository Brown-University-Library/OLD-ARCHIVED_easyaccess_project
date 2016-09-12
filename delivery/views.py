# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, os, pprint, urlparse
from datetime import datetime

import bibjsontools, markdown, requests
from bibjsontools import from_dict, from_openurl, to_openurl
from common_classes.illiad_helper import IlliadHelper
from delivery import app_settings
from delivery.classes.availability_helper import AvailabilityViewHelper
from delivery.classes.availability_helper import JosiahAvailabilityChecker
from delivery.classes.login_helper import LoginViewHelper
from delivery.classes.process_helper import ProcessViewHelper
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import redirect, render
from django.template import Context
from django.template import loader
from django.utils.decorators import method_decorator
from django.utils.http import urlquote
from django.views.generic import TemplateView
from py360link2 import get_sersol_data, Resolved
from utils import DeliveryBaseView, JSONResponseMixin, merge_bibjson, illiad_validate


log = logging.getLogger('access')
SERSOL_KEY = settings.BUL_LINK_SERSOL_KEY
availability_view_helper = AvailabilityViewHelper()
illiad_helper = IlliadHelper()
login_view_helper = LoginViewHelper()
# process_view_helper = ProcessViewHelper()


def availability( request ):
    """ Manages borrow landing page where availability checks happen.
        Should get here after landing at 'find' urls, when item is a book. """
    log_id = request.session.get( 'log_id', '' )
    querystring = request.META.get('QUERY_STRING', '').decode('utf-8')
    log.debug( '`{id}` starting; querystring, `{val}`'.format(id=log_id, val=querystring) )
    log.debug( '`{id}` availability() starting session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )

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
    if 'identifier' in bib_dct.keys():
        for identifier in bib_dct['identifier']:
            if identifier['type'] == 'isbn':
                isbn = identifier['id']
            elif identifier['type'] == 'oclc':
                oclc_num = identifier['id']
    bib_dct['isbn'] = isbn
    bib_dct['oclc_num'] = oclc_num
    request.session['bib_dct_json'] = json.dumps(bib_dct)

    ## run recent-request check -- TODO

    ## run josiah availability check
    availability_checker = JosiahAvailabilityChecker()
    available_holdings = availability_checker.check_josiah_availability( isbn, oclc_num )
    bib_num = availability_checker.bib_num

    ## set available flag
    available_locally = False
    if len( available_holdings ) > 0:
        available_locally = True

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
        'openurl': querystring,  # for export to refworks
        'ebook_dct': ebook_dct,
        'ris_url': '{ris_url}?{eq}'.format( ris_url=reverse('findit:ris_url'), eq=querystring )
        }
    log.debug( '`{id}` availability() ending session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )

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


def shib_login( request ):
    """ Tries an sp login, which returns to the login_handler() url.
        Called when views.availability() returns a Request button that's clicked.
        Session cleared and info put in url due to revproxy resetting session. """
    log_id = request.session.get( 'log_id', '' )
    log.debug( '`{id}` starting session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )

    bib_dct_json = request.session['bib_dct_json']
    last_querystring = request.session['last_querystring']
    permalink_url = request.session['permalink_url']

    ## clear session so we know that regular-processing happens same way as revproxy-processing
    for key in request.session.keys():
        del request.session[key]
    log.debug( '`{id}` session.items() after deletion, ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )

    ## build login_handler url
    # login_handler_querystring = 'bib_dct_json={bdj}&last_querystring={lq}&permalink_url={pml}'.format(
    #     bdj=urlquote(bib_dct_json), lq=urlquote(last_querystring), pml=urlquote(permalink_url) )
    login_handler_querystring = 'bib_dct_json={bdj}&last_querystring={lq}&permalink_url={pml}&ezlogid={id}'.format(
        bdj=urlquote(bib_dct_json), lq=urlquote(last_querystring), pml=urlquote(permalink_url), id=log_id )
    log.debug( '`{id}` len(login_handler_querystring), ```{val}```'.format(id=log_id, val=len(login_handler_querystring)) )

    login_handler_url = '{scheme}://{host}{login_handler_url}?{querystring}'.format(
        scheme=request.scheme, host=request.get_host(), login_handler_url=reverse('delivery:login_handler_url'), querystring=login_handler_querystring )
    log.debug( 'pre-encoded login_handler_url, ```{}```'.format(login_handler_url) )

    localdev_check = False
    if request.get_host() == '127.0.0.1' and settings.DEBUG2 == True:  # eases local development
        localdev_check = True

    if localdev_check is True:
        log.debug( 'localdev_check is True, redirecting right to pre-encoded login_handler' )
        return HttpResponseRedirect( login_handler_url )
    else:
        encoded_login_handler_url = urlquote( login_handler_url )
        redirect_url = '{shib_login}?target={encoded_login_handler_url}'.format(
            shib_login=app_settings.SHIB_LOGIN_URL, encoded_login_handler_url=encoded_login_handler_url )
        log.debug( 'redirect_url to shib-sp-login, ```{}```'.format(redirect_url) )
        return HttpResponseRedirect( redirect_url )


def login_handler( request ):
    """ User redirected here from shib_login().
        (for now)
        - stores shib info to session
        - redirects user to process_request url/view
        (eventually)
        - gets or creates user-object and library-profile-data
        - redirects user to process_request url/view """

    ## check referrer
    log_id = request.GET.get( 'ezlogid', '' )
    log.debug( '`{id}` request.__dict__, ```{val}```'.format(id=log_id, val=pprint.pformat(request.__dict__)) )
    log.debug( '`{id}` starting session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )
    # ( referrer_ok, redirect_url ) = login_view_helper.check_referrer( request.session, request.META )
    # if referrer_ok is not True:
    #     request.session['last_path'] = request.path
    #     return HttpResponseRedirect( redirect_url )
    request.session['last_path'] = request.path

    ## rebuild session (revproxy can destroy it, so all info must be in request.GET)
    request.session['log_id'] = log_id
    request.session['bib_dct_json'] = request.GET['bib_dct_json']

    last_querystring = login_view_helper.check_querystring( request.GET['last_querystring'] )

    request.session['last_querystring'] = last_querystring
    request.session['permalink_url'] = request.GET.get( 'permalink_url', '' )
    log.debug( 'session.items() after rebuild, ```{}```'.format(pprint.pformat(request.session.items())) )

    ## update bib_dct_json if needed -- TODO: redo, since availability posts to shib_login(), not login_hander()
    # easyborrow_volumes = request.POST.get( 'volumes', '' ).strip()
    # if easyborrow_volumes != '':
    #     bib_dct = request.session.get( 'bib_dct_json', {} )
    #     bib_dct['easyborrow_volumes'] = easyborrow_volumes
    #     request.session['bib_dct_json'] = json.dumps( bib_dct )

    ## update user/profile objects
    localdev_check = False
    if request.get_host() == '127.0.0.1' and settings.DEBUG2 == True:  # eases local development
        localdev_check = True
    log.debug( 'localdev_check, `{}`'.format(localdev_check) )
    shib_dct = login_view_helper.update_user( localdev_check, request.META, request.get_host() )  # will eventually return user object
    request.session['user_json'] = json.dumps( shib_dct )

    log.debug( '`{id}` ending session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )

    ## redirect to process_request
    redirect_url = '{root_url}?{querystring}'.format( root_url=reverse('delivery:process_request_url'), querystring=request.session.get('last_querystring', '') )
    return HttpResponseRedirect( redirect_url )


# def login_handler( request ):
#     """ User redirected here from shib_login().
#         (for now)
#         - stores shib info to session
#         - redirects user to process_request url/view
#         (eventually)
#         - gets or creates user-object and library-profile-data
#         - redirects user to process_request url/view """

#     ## check referrer
#     log_id = request.GET.get( 'ezlogid', '' )
#     log.debug( '`{id}` request.__dict__, ```{val}```'.format(id=log_id, val=pprint.pformat(request.__dict__)) )
#     log.debug( '`{id}` starting session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )
#     # ( referrer_ok, redirect_url ) = login_view_helper.check_referrer( request.session, request.META )
#     # if referrer_ok is not True:
#     #     request.session['last_path'] = request.path
#     #     return HttpResponseRedirect( redirect_url )
#     request.session['last_path'] = request.path

#     ## rebuild session (revproxy can destroy it, so all info must be in querystring)
#     request.session['log_id'] = log_id
#     request.session['bib_dct_json'] = request.GET['bib_dct_json']
#     request.session['last_querystring'] = request.GET['last_querystring']
#     request.session['permalink_url'] = request.GET.get( 'permalink_url', '' )
#     log.debug( 'session.items() after rebuild, ```{}```'.format(pprint.pformat(request.session.items())) )

#     ## update bib_dct_json if needed -- TODO: redo, since availability posts to shib_login(), not login_hander()
#     # easyborrow_volumes = request.POST.get( 'volumes', '' ).strip()
#     # if easyborrow_volumes != '':
#     #     bib_dct = request.session.get( 'bib_dct_json', {} )
#     #     bib_dct['easyborrow_volumes'] = easyborrow_volumes
#     #     request.session['bib_dct_json'] = json.dumps( bib_dct )

#     ## update user/profile objects
#     localdev_check = False
#     if request.get_host() == '127.0.0.1' and settings.DEBUG2 == True:  # eases local development
#         localdev_check = True
#     log.debug( 'localdev_check, `{}`'.format(localdev_check) )
#     shib_dct = login_view_helper.update_user( localdev_check, request.META, request.get_host() )  # will eventually return user object
#     request.session['user_json'] = json.dumps( shib_dct )

#     log.debug( '`{id}` ending session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )

#     ## redirect to process_request
#     redirect_url = '{root_url}?{querystring}'.format( root_url=reverse('delivery:process_request_url'), querystring=request.session.get('last_querystring', '') )
#     return HttpResponseRedirect( redirect_url )


def process_request( request ):
    """ User redirected here from login_handler().
        (for now)
        - Saves data to easyBorrow db
        - redirects user (behind-the-scenes) to SP shib-logout ( which will then direct user to views.message() )
        (eventually)
        - Creates resource object, then
        - grabs user object
        - checks for recent request
        - saves data to easyBorrow db
        - redirects user to message url/view """

    log_id = request.session.get('log_id', '')
    log.debug( '`{id}` starting session.items(), ```{val}```'.format(id=log_id, val=pprint.pformat(request.session.items())) )

    process_view_helper = ProcessViewHelper( log_id )

    ## check referrer
    ( referrer_ok, redirect_url ) = process_view_helper.check_referrer( request.session, request.META )
    request.session['last_path'] = request.path
    if referrer_ok is False:
        # request.session['message'] = 'Sorry, there was a problem with that url. easyBorrow requests should start _here_; contact us if this problem continues.'
        return HttpResponseRedirect( redirect_url )

    ## check if authorized
    shib_dct = json.loads( request.session.get('user_json', '{}') )
    ( is_authorized, redirect_url, message ) = process_view_helper.check_if_authorized( shib_dct )
    if is_authorized is False:
        log.info( '`{id}` user, `{val}` not authorized; redirecting to shib-logout-url, then message-url'.format(id=log_id, val=shib_dct.get('eppn', 'no_eppn')) )
        request.session['message'] = message
        return HttpResponseRedirect( redirect_url )

    ## get/create resource object
    # resource_obj = process_view_helper.grab_resource( querystring )

    ## get user object
    # user_obj = process_view_helper.grab_user( request.META.get('Shibboleth-eppn', '') )

    ## check for recent request
    # if process_view_helper.check_recently_requested( user_obj, resource_obj ) is True:
    #     request.session['message'] = "You've recently requested this item and should soon receive an update email."
    #     return HttpResponseRedirect( reverse('delivery:message_url') )

    ## check for new-user
    # shib_dct = json.loads( request.session.get('user_json', '{}') )
    try:
        illiad_helper.check_illiad( shib_dct )
    except Exception as e:
        log.error( 'exception checking illiad for new-user, ```{}```'.format(unicode(repr(e))) )

    ## save new request
    # process_view_helper.save_request( user_obj, resource_obj )
    # shib_dct = json.loads( request.session.get('user_json', '{}') )
    bib_dct = json.loads( request.session.get('bib_dct_json', '{}') )
    ezb_db_id = process_view_helper.save_to_easyborrow( shib_dct, bib_dct, request.session.get('last_querystring', '') )

    ## evaluate result
    if ezb_db_id:
        message = process_view_helper.build_submitted_message( shib_dct['name_first'], shib_dct['name_last'], bib_dct, ezb_db_id, shib_dct['email'] )
    else:
        message = "There was a problem submitting your request, please try again in a few minutes, and if the problem persists, let us know via the feedback link."

    ## redirect to shib-logout url (which will redirect to message-url)
    request.session['message'] = message
    redirect_url = '{main_url}?{querystring}'.format(
        main_url=reverse('delivery:shib_logout_url'), querystring=request.META.get('QUERY_STRING', '').decode('utf-8') )
    log.debug( 'redirect_url, ```{}```'.format(redirect_url) )
    return HttpResponseRedirect( redirect_url )


def shib_logout( request ):
    """ Clears session; builds SP shib-logout url, with target of 'borrow/message/'; redirects. """
    log_id = request.session.get( 'log_id', '' )
    message = request.session.get( 'message', '' )
    permalink_url = request.session.get( 'permalink_url', '' )
    last_querystring = request.session.get( 'last_querystring', '' )
    logout( request )  # from django.contrib.auth import logout
    request.session['log_id'] = log_id
    request.session['message'] = message
    request.session['permalink_url'] = permalink_url
    request.session['last_querystring'] = last_querystring
    process_view_helper = ProcessViewHelper( log_id )
    redirect_url = process_view_helper.build_shiblogout_redirect_url( request )
    log.debug( '`{id}` redirect_url, `{val}`'.format(id=log_id, val=redirect_url) )
    return HttpResponseRedirect( redirect_url )


def message( request ):
    """ Handles successful confirmation messages and problem messages. """
    log_id = request.session.get( 'log_id', '' )
    permalink_url = request.session.get( 'permalink_url', '' )
    querystring = request.session.get( 'last_querystring', '' )
    context = {
        'last_path': request.session.get( 'last_path', '' ),
        'message': markdown.markdown( request.session.get('message', '') ),
        'permalink_url': permalink_url,
        'report_problem_url': availability_view_helper.build_problem_report_url( permalink_url, request.META.get('REMOTE_ADDR', 'ip_not_available') ),
        'openurl': querystring,  # for export to refworks
        'ris_url': '{ris_url}?{eq}'.format( ris_url=reverse('findit:ris_url'), eq=querystring ),
        }
    log.debug( '`{id}` message context, ```{val}```'.format(id=log_id, val=pprint.pformat(context)) )
    request.session['message'] = ''
    request.session['last_path'] = request.path
    # logout( request )  # from django.contrib.auth import logout
    return render( request, 'delivery/message.html', context )


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

