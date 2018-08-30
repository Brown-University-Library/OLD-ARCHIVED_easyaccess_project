# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
import bibjsontools, requests
from django.utils.encoding import uri_to_iri
from delivery import app_settings


log = logging.getLogger('access')


class AvailabilityViewHelper(object):
    """ Holds helpers for views.availability() """

    def build_problem_report_url( self, permalink, ip ):
        """ Builds problem/feedback url.
            Called by views.availability() """
        problem_url = '{problem_form_url_root}?formkey={problem_form_key}&entry_2={permalink}&entry_3={ip}'.format(
            problem_form_url_root=app_settings.PROBLEM_FORM_URL_ROOT,
            problem_form_key=app_settings.PROBLEM_FORM_KEY,
            permalink=permalink,
            ip=ip )
        log.debug( 'problem_url, ```{}```'.format(problem_url) )
        return problem_url

    def build_bib_dct( self, querystring ):
        """ Calls bibjsontools.
            Called by views.availability() """
        log.debug( 'querystring, ```{}```'.format(querystring) )
        log.debug( 'type(querystring), `{}`'.format(type(querystring)) )
        assert type(querystring) == unicode
        iri_querystring = uri_to_iri( querystring )
        bib_dct = bibjsontools.from_openurl( iri_querystring )
        log.debug( 'bib_dct, ```{}```'.format(pprint.pformat(bib_dct)) )
        return bib_dct

    ## end class AvailabilityViewHelper()


class JosiahAvailabilityChecker(object):
    """ Manages check for item-availability. """

    def __init__( self ):
        self.available_bibs = []
        self.available_holdings = []

    def run_isbn_search( self, isbn ):
        """ Runs availability-api isbn search.
            Called by check_josiah_availability() """
        if isbn is None:
            return
        api_isbn_url = '%s/isbn/%s' % ( app_settings.AVAILABILITY_URL_ROOT, isbn )
        log.debug( 'api_isbn_url, ```%s```' % api_isbn_url )
        try:
            r = requests.get( isbn_url, timeout=10 )
            api_jdct = json.loads( r.content.decode('utf-8') )
            log.debug( 'isbn-jdct, ```%s```' % pprint.pformat(jdct) )
            self.store_available_bibs( api_jdct )
        except Exception as e:
            log.warning( 'isbn-availability-check may have timed out, error, ```%s```' % unicode(repr(e)) )

        bib_num = jdct.get( 'id', None )
        if bib_num:
            self.bib_num = bib_num
            for item in jdct['items']:
                if item['is_available'] is True:
                    isbn_item = {'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability']}
                    log.debug( 'isbn_item being added, {}'.format(isbn_item) )
                    available_holdings.append( isbn_item )

    def store_available_bibs( self, api_jdct ):
        """ Updates self.available_bibs
            Called by run_isbn_search() and run_oclc_search() """
        available_bibs = api_jdct['response']['basics']['ezb_available_bibs']
        for bib in available_bibs:
            if bib not in self.available_bibs:
                self.available_bibs.append( bib )


    def check_josiah_availability( self, isbn, oclc_num ):
        """ Checks josiah availability, updates self.bibs, returns holdings data.
            Called by views.availability() """
        available_holdings = []
        self.run_isbn_search( isbn )
        if oclc_num and available_holdings == []:
            oclc_num_url = '{ROOT}oclc/{OCLC_NUM}/'.format( ROOT=app_settings.AVAILABILITY_URL_ROOT, OCLC_NUM=oclc_num )
            log.debug( 'oclc_num_url, `{}`'.format(oclc_num_url) )
            try:
                r = requests.get( oclc_num_url, timeout=10 )
                oclc_jdct = json.loads( r.content.decode('utf-8') )
                log.debug( 'oclc_jdct, ```{}```'.format(pprint.pformat(oclc_jdct)) )
            except Exception as e:
                log.warning( 'oclc-availability-check may have timed out, error, ```{}```'.format(unicode(repr(e))) )
                oclc_jdct = {}
            bib_num = oclc_jdct.get( 'id', None )
            if bib_num:
                self.bib_num = bib_num
                for item in oclc_jdct['items']:
                    if item['is_available'] is True:
                        # oclc_num_callnumber = item['callnumber']
                        # match_check = False
                        # for holding in available_holdings:
                        #     log.debug( 'holding being checked, ```{}```'.format(holding) )
                        #     if oclc_num_callnumber == holding['callnumber']:
                        #         match_check = True
                        #         break
                        # if match_check is False:
                        #     additional_oclc_item = {'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability']}
                        #     log.debug( 'additional_oclc_item being added, {}'.format(additional_oclc_item) )
                        #     available_holdings.append( additional_oclc_item )
                        oclc_item = { 'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability'] }
                        log.debug( 'oclc_item being added, {}'.format(oclc_item) )
                        available_holdings.append( oclc_item )
        log.debug( 'available_holdings, ```%s```' % pprint.pformat(available_holdings) )
        return available_holdings

    ## end class JosiahAvailabilityChecker()

# class JosiahAvailabilityChecker(object):
#     """ Manages check for item-availability. """

#     def __init__( self ):
#         self.bib_num = ''

#     def check_josiah_availability( self, isbn, oclc_num ):
#         """ Checks josiah availability, returns holdings data.
#             Called by views.availability() """
#         available_holdings = []
#         jdct = {}
#         if isbn:
#             isbn_url = '{ROOT}isbn/{ISBN}/'.format( ROOT=app_settings.AVAILABILITY_URL_ROOT, ISBN=isbn )
#             log.debug( 'isbn_url, ```{}```'.format(isbn_url) )
#             try:
#                 r = requests.get( isbn_url, timeout=10 )
#                 jdct = json.loads( r.content.decode('utf-8') )
#                 log.debug( 'isbn-jdct, ```{}```'.format(pprint.pformat(jdct)) )
#             except Exception as e:
#                 log.warning( 'isbn-availability-check may have timed out, error, ```{}```'.format(unicode(repr(e))) )
#             bib_num = jdct.get( 'id', None )
#             if bib_num:
#                 self.bib_num = bib_num
#                 for item in jdct['items']:
#                     if item['is_available'] is True:
#                         isbn_item = {'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability']}
#                         log.debug( 'isbn_item being added, {}'.format(isbn_item) )
#                         available_holdings.append( isbn_item )
#         if oclc_num and available_holdings == []:
#             oclc_num_url = '{ROOT}oclc/{OCLC_NUM}/'.format( ROOT=app_settings.AVAILABILITY_URL_ROOT, OCLC_NUM=oclc_num )
#             log.debug( 'oclc_num_url, `{}`'.format(oclc_num_url) )
#             try:
#                 r = requests.get( oclc_num_url, timeout=10 )
#                 oclc_jdct = json.loads( r.content.decode('utf-8') )
#                 log.debug( 'oclc_jdct, ```{}```'.format(pprint.pformat(oclc_jdct)) )
#             except Exception as e:
#                 log.warning( 'oclc-availability-check may have timed out, error, ```{}```'.format(unicode(repr(e))) )
#                 oclc_jdct = {}
#             bib_num = oclc_jdct.get( 'id', None )
#             if bib_num:
#                 self.bib_num = bib_num
#                 for item in oclc_jdct['items']:
#                     if item['is_available'] is True:
#                         # oclc_num_callnumber = item['callnumber']
#                         # match_check = False
#                         # for holding in available_holdings:
#                         #     log.debug( 'holding being checked, ```{}```'.format(holding) )
#                         #     if oclc_num_callnumber == holding['callnumber']:
#                         #         match_check = True
#                         #         break
#                         # if match_check is False:
#                         #     additional_oclc_item = {'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability']}
#                         #     log.debug( 'additional_oclc_item being added, {}'.format(additional_oclc_item) )
#                         #     available_holdings.append( additional_oclc_item )
#                         oclc_item = { 'callnumber': item['callnumber'], 'location': item['location'], 'status': item['availability'] }
#                         log.debug( 'oclc_item being added, {}'.format(oclc_item) )
#                         available_holdings.append( oclc_item )
#         log.debug( 'available_holdings, ```%s```' % pprint.pformat(available_holdings) )
#         return available_holdings

#     ## end class JosiahAvailabilityChecker()
