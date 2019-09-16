# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint, random, urllib
from urllib.parse import urlparse, unquote
import requests
from article_request_app import settings_app
from common_classes.illiad_helper import IlliadHelper as CommonIlliadHelper
from django.core.urlresolvers import reverse


log = logging.getLogger('access')
common_illiad_helper = CommonIlliadHelper()


class IlliadArticleSubmitter( object ):
    """ Contains code for views.illiad_handler() to actually submit the article request to ILLiad. """

    def __init__(self):
        self.log_id = '%s' % random.randint(10000, 99999)  # helps to track processing

    # def enhance_if_necessary( self, illiad_url ):
    #     """ Examines basic title/author info and attempts to populate it from other fields if available.
    #         Called by views.illiad_handler() """
    #     # TODO -- no, enhancing in findit-app, cuz that's where the illiad-openurl is built
    #     log.debug( f'initial illiad_url, ```{illiad_url}```' )
    #     log.debug( f'returning illiad_url, ```{illiad_url}```' )
    #     return illiad_url

    def prepare_submit_params( self, usr_dct, illiad_full_url ):
        """ Builds parameter_dict for the internal api hit.
            Called by views.illiad_handler() """
        param_dct = {
            'auth_key': settings_app.ILLIAD_API_KEY,  # required
            'request_id': self.log_id,  # required
            'first_name': usr_dct['name_first'],
            'last_name': usr_dct['name_last'],
            'username': usr_dct['eppn'].split('@')[0],  # required
            'address': '',
            'email': usr_dct['email'],
            'oclc_number': '',  # easyBorror tries to submit this
            # 'openurl': self.make_openurl_segment( item_inst.knowledgebase_openurl, item_inst.volumes_info, patron_inst.barcode ),
            'openurl': self.grab_openurl_from_illiad_full_url( illiad_full_url ),  # required
            'patron_barcode': usr_dct['patron_barcode'],
            'patron_department': '',
            'patron_status': '',
            'phone': '',
            # 'volumes': '',
        }
        log.debug( '`%s` - param_dct, ```%s```' % (self.log_id, pprint.pformat(param_dct)) )
        return param_dct

    def grab_openurl_from_illiad_full_url( self, illiad_full_url ):
        """ Takes the query part of the url, since this was enhanced in the findit app to include useful 'Notes'.
            Called by prepare_submit_params() """
        # parse_obj = urlparse.urlparse( illiad_full_url )  # py2
        parse_obj = urlparse( illiad_full_url )
        querystring = parse_obj.query
        log.debug( '`%s` - querystring, ```%s```' % (self.log_id, querystring) )
        log.debug( 'type(querystring), `%s`' % type(querystring) )
        decoded_querystring = unquote( querystring )
        log.debug( '`%s` - decoded_querystring, ```%s```' % (self.log_id, decoded_querystring) )
        return decoded_querystring

    def submit_request( self, param_dct ):
        """ Hits api.
            Called by views.illiad_handler() """
        try:
            url = '%s%s' % ( settings_app.ILLIAD_API_URL_ROOT, 'request_article/' )
            headers = { 'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8' }
            r = requests.post( url, data=param_dct, headers=headers, timeout=60, verify=True )
            api_response_text = r.content.decode('utf-8', 'replace')
            log.debug( '`%s` - api response text, ```%s```' % (self.log_id, api_response_text) )
            submission_response_dct = self.prep_response_dct( api_response_text )
            return submission_response_dct
        except Exception as e:
            # log.error( '`%s` - exception on illiad-article-submission, ```%s```' % (self.log_id, unicode(repr(e))) )
            log.exception( f'{self.log_id} - exception on illiad-article-submission; traceback follows, but problem-message will be created and returned to user.' )
            submission_response_dct = { 'success': False, 'error_message': self.prep_submission_problem_message() }
            # log.debug( '`%s` - error submission_response_dct, ```%s```' % (self.log_id, pprint.pformat(submission_response_dct)) )
            log.debug( f'`{self.log_id}` - error submission_response_dct, ```{pprint.pformat(submission_response_dct)}```' )
            return submission_response_dct

    def prep_response_dct( self, api_response_text ):
        """ Assesses api response and prepares data for view.
            Called by submit_request() """
        jdct = json.loads( api_response_text )
        submission_response_dct = { 'success': False, 'error_message': self.prep_submission_problem_message() }  # just initializing
        if jdct.get( 'status', None ) == 'submission_successful':
            if jdct.get( 'transaction_number', None ):
                submission_response_dct = { 'success': True, 'transaction_number': jdct['transaction_number'] }
        log.debug( '`%s` - submission_response_dct, ```%s```' % (self.log_id, pprint.pformat(submission_response_dct)) )
        return submission_response_dct

    def prep_submission_problem_message( self ):
        problem_message = """
Your request was not able to be submitted to ILLiad, our Interlibrary Loan system.

Please try again later. If the problem persists, there may be an issue with your ILLiad account, in which case,

you may contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169.

The staff will work with you to resolve the problem.

Apologies for the inconvenience.
"""
        return problem_message

    ## end class IlliadArticleSubmitter()


class IlliadApiHelper( object ):
    """ Contains helpers for views.login_handler() (for now; more later).
        Purpose is to use this to transition away from pip-installed illiad module to illiad-api-webservice calls. """

    def __init__(self):
        pass

    # def manage_illiad_user_check( self, usr_dct, title ):
    #     """ Manager for illiad handling.
    #         - hits the new illiad-api for the status (`blocked`, `registered`, etc)
    #             - if problem, prepares failure message as-is (creating return-dct)
    #             - if new-user, runs manage_new_user() and creates proper success or failure return-dct
    #             - if neither problem or new-user, TODO -- incorporate the new update-status api call here
    #         Called by views.login_handler()...
    #           ...which, on any failure, will store the returned crafted error message to the session,
    #           ...and redirect to an error page. """
    #     log.debug( '(article_request_app) - usr_dct, ```%s```' % pprint.pformat(usr_dct) )
    #     illiad_status_dct = self.check_illiad_status( usr_dct['eppn'].split('@')[0] )
    #     if illiad_status_dct['response']['status_data']['blocked'] is True or illiad_status_dct['response']['status_data']['disavowed'] is True:
    #         return_dct = self.make_illiad_problem_message( usr_dct, title )
    #     elif illiad_status_dct['response']['status_data']['interpreted_new_user'] is True:
    #         return_dct = self.manage_new_user( usr_dct, title )
    #     else:
    #         return_dct = { 'success': True }
    #     log.debug( 'return_dct, ```%s```' % pprint.pformat(return_dct) )
    #     return return_dct

    def manage_illiad_user_check( self, usr_dct, title ):
        """ Manager for illiad handling.
            - hits the new illiad-api for the status (`blocked`, `registered`, etc)
                - if problem, prepares failure message as-is (creating return-dct)
                - if new-user, runs manage_new_user() and creates proper success or failure return-dct
                - if neither problem or new-user, TODO -- incorporate the new update-status api call here
            Called by views.login_handler()...
              ...which, on any failure, will store the returned crafted error message to the session,
              ...and redirect to an error page. """
        log.debug( '(article_request_app) - usr_dct, ```%s```' % pprint.pformat(usr_dct) )
        illiad_status_dct = self.check_illiad_status( usr_dct['eppn'].split('@')[0] )
        if illiad_status_dct['response']['status_data']['blocked'] is True or illiad_status_dct['response']['status_data']['disavowed'] is True:
            return_dct = self.make_illiad_problem_message( usr_dct, title )
        elif 'interpreted_new_user' in illiad_status_dct['response']['status_data'].keys():  # temp handling during illiad switch-over
            if illiad_status_dct['response']['status_data']['interpreted_new_user'] is True:
                return_dct = self.manage_new_user( usr_dct, title )
            else:
                return_dct = { 'success': True }
        else:
            return_dct = { 'success': True }
        log.debug( 'return_dct, ```%s```' % pprint.pformat(return_dct) )
        return return_dct

    def check_illiad_status( self, auth_id ):
        """ Hits our internal illiad-api for user's status (`blocked`, `registered`, etc).
            Called by manage_illiad_user_check() """
        rspns_dct = { 'response':
            {'status_data': {'blocked': None, 'disavowed': None}} }
        url = '%s%s' % ( settings_app.ILLIAD_API_URL_ROOT, 'check_user/' )
        params = { 'user': auth_id }
        try:
            r = requests.get( url, params=params, auth=(settings_app.ILLIAD_API_BASIC_AUTH_USER, settings_app.ILLIAD_API_BASIC_AUTH_PASSWORD), verify=True, timeout=10 )
            rspns_dct = r.json()
            log.debug( 'status_code, `%s`; content-dct, ```%s```' % (r.status_code, pprint.pformat(rspns_dct)) )
        except Exception as e:
            log.error( 'error on status check, ```%s```' % repr(e) )
        return rspns_dct

    def manage_new_user( self, usr_dct, title ):
        """ Manages new-user creation and response-assessment.
            Called by manage_illiad_user_check() """
        success_check = self.create_new_user( usr_dct )
        if not success_check == True:
            return_dct = self.make_illiad_unregistered_message( usr_dct, title )
        else:
            return_dct = { 'success': True }
        log.debug( 'return_dct, ```%s```' % pprint.pformat(return_dct) )
        return return_dct

    def create_new_user( self, usr_dct ):
        """ Hits internal api to create new user.
            Called by manage_new_user() """
        ( params, success_check, url ) = self.setup_create_user( usr_dct )
        try:
            r = requests.post( url, data=params, verify=True, timeout=10 )
            log.debug( 'status_code, `%s`; content, ```%s```' % (r.status_code, r.content.decode('utf-8', 'replace')) )
            result = r.json()['response']['status_data']['status'].lower()
            if result == 'registered':
                success_check = True
        except Exception as e:
            # log.error( 'Exception on new user registration, ```%s```' % unicode(repr(e)) )  ## success_check already initialized to False
            log.exception( f'(article_request_app) - exception on new user registration; traceback follows, but processing will continue' )
        log.debug( 'success_check, `%s`' % success_check )
        return success_check

    def setup_create_user( self, usr_dct ):
        """ Initializes vars.
            Called by create_new_user() """
        params = {
            'auth_key': settings_app.ILLIAD_API_KEY,
            'auth_id': usr_dct['eppn'].split('@')[0],
            'first_name': usr_dct['name_first'],
            'last_name': usr_dct['name_last'],
            'email': usr_dct['email'],
            'status': usr_dct['brown_type'],
            'phone': usr_dct['phone'],
            'department': usr_dct['department'] }
        success_check = False
        url = '%s%s' % ( settings_app.ILLIAD_API_URL_ROOT, 'create_user/' )
        log.debug( 'params, ```%s```; success_check, `%s`; url, ```%s```' % (pprint.pformat(params), success_check, url) )
        return ( params, success_check, url )

    ## ======================================
    ## IlliadApiHelper() problem messages (2)
    ## ======================================

    def make_illiad_problem_message( self, usr_dct, title ):
        """ Preps illiad blocked message.
            Called by _check_blocked() """
        ( firstname, lastname ) = ( usr_dct['name_first'], usr_dct['name_last'] )
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyArticle service. It appears there is a problem with your Interlibrary Loan, ILLiad account.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    '''.strip() % (
        firstname,
        lastname,
        title )
        # log.debug( 'illiad blocked message built, ```%s```' % message )
        rtrn_dct = { 'error_message': message, 'success': False }
        log.debug( 'rtrn_dct, ```%s```' % pprint.pformat(rtrn_dct) )
        return rtrn_dct
        ## end def make_illiad_problem_message()

    def make_illiad_unregistered_message( self, firstname, lastname, title ):
        """ Preps illiad blocked message.
            Called by _handle_new_user() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyAccess service. There was a problem trying to register you with 'ILLiad', our interlibrary-loan service.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    ''' % (
        firstname,
        lastname,
        title )
        # log.debug( 'illiad unregistered message built, ```%s```' % message )
        rtrn_dct = { 'error_message': message, 'success': False }
        log.debug( 'rtrn_dct, ```%s```' % pprint.pformat(rtrn_dct) )
        return rtrn_dct
        ## end def make_illiad_unregistered_message()

    ## end class IlliadApiHelper()


class NewIlliadHelper( object ):
    """ Contains helpers for views.illiad_request(), views.login() and views.illiad_handler()
        New code with unit-tests.
        Under construction. """

    def __init__(self):
        self.problem_message = """
Your request was not able to be submitted to ILLiad, our Interlibrary Loan system.

Please try again later. If the problem persists, there may be an issue with your ILLiad account.

Contact Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

Apologies for the inconvenience.
"""

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /find/.
            Called by views.illiad_request() """
        # ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
        ( referrer_ok, redirect_url, last_path ) = ( False, '', session_dct.get('last_path', '') )
        log.debug( 'last_path, `{}`'.format(last_path) )
        # if last_path == '/easyaccess/article_request/login_handler/' or last_path == '/article_request/login_handler/':  # production vs dev-runserver; TODO: handle better.
        if '/article_request/login_handler/' in last_path:
            referrer_ok = True
        if referrer_ok is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
        return ( referrer_ok, redirect_url )

    def _prepare_failure_message( self, connect_result_dct, user_dct, title, return_dct ):
        """ Sets return error_message on connect/login failure.
            Called by login_user() """
        if connect_result_dct['error_message'] is not None:
            return_dct['error_message'] = connect_result_dct['error_message']
        elif connect_result_dct['is_blocked'] is True:
            return_dct['error_message'] = self.make_illiad_blocked_message( user_dct['name_first'], user_dct['name_last'], title )
        log.debug( 'return_dct, ```{}```'.format(pprint.pformat(return_dct)) )
        return return_dct

    ##########################
    ### illiad blocked message
    ##########################
    def make_illiad_blocked_message( self, firstname, lastname, title ):
        """ Preps illiad blocked message.
            Called by _check_blocked() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyArticle service. It appears there is a problem with your Interlibrary Loan, ILLiad account.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    '''.strip() % (
        firstname,
        lastname,
        title )
        log.debug( 'illiad blocked message built, ```%s```' % message )
        return message

    ###############################
    ### illiad unregistered message
    ###############################
    def make_illiad_unregistered_message( self, firstname, lastname, title ):
        """ Preps illiad blocked message.
            Called by _handle_new_user() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyAccess service. There was a problem trying to register you with 'ILLiad', our interlibrary-loan service.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    ''' % (
        firstname,
        lastname,
        title )
        log.debug( 'illiad unregistered message built, ```%s```' % message )
        return message

    ##########################
    ### illiad success message
    ##########################
    def make_illiad_success_message( self, firstname, lastname, title, illiad_transaction_number, email ):
        """ Preps illiad success message.
            Called by views.illiad_handler() """
        message = '''
Greetings {firstname} {lastname},

We're getting the title '{title}' for you. You'll be notified when it arrives.

Some useful information for your records:

- Title: '{title}'
- Ordered from service: 'ILLiad'
- Your Illiad reference number: '{illiad_num}'
- Notification of arrival will be sent to email address: <{email}>

You can check your Illiad account at the link:
<https://brown.illiad.oclc.org/illiad/>

If you have any questions, contact the Library's Interlibrary Loan office at <interlibrary_loan@brown.edu> or call 401-863-2169.

  '''.format(
        firstname=firstname,
        lastname=lastname,
        title=title,
        illiad_num=illiad_transaction_number,
        email=email )
        log.debug( 'illiad success message built' )
        return message

    ## end class NewIlliadHelper
