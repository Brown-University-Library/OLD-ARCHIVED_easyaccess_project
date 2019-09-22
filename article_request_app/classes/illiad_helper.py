# -*- coding: utf-8 -*-

import json, logging, pprint, random, urllib
from urllib.parse import parse_qs, urlparse, unquote

import bibjsontools, requests
from article_request_app import settings_app
from common_classes import misc
from django.core.urlresolvers import reverse


log = logging.getLogger('access')
# common_illiad_helper = CommonIlliadHelper()



class IlliadUrlBuilder( object ):
    """ Constructs url sent to illiad.
        Called by FinditResolver() code. """

    def __init__( self ):
        self.validator = IlliadValidator()

    def make_illiad_url( self, original_querystring, enhanced_querystring, scheme, host, permalink ):
        """ Manages steps of constructing illiad url for possible use in article-requesting.
            Called by views.illiad_handler()
            TODO: The scheme://host is no longer used, now that the illiad-api is hit; that should be phased out from the code and settings. """
        bib_dct = bibjsontools.from_openurl( enhanced_querystring )
        log.debug( f'bib_dct, ```{pprint.pformat(bib_dct)}```' )
        ill_bib_dct = self.validator.add_required_kvs( bib_dct )
        extra_dct = self.check_identifiers( ill_bib_dct )
        extra_dct = self.check_validity( ill_bib_dct, extra_dct )
        log.debug( f'bib_dct before enhance, ```{ill_bib_dct}```' )
        ill_bib_dct = self.enhance_citation( ill_bib_dct, original_querystring )
        log.debug( f'bib_dct after enhance, ```{ill_bib_dct}```' )
        full_permalink = '%s://%s%s' % ( scheme, host, permalink )
        extra_dct['Notes'] = self.update_note( extra_dct.get('Notes', ''), '`shortlink: <%s>`' % full_permalink )
        openurl = bibjsontools.to_openurl( ill_bib_dct )
        log.debug( f'openurl from bibjsontools, ```{openurl}```' )
        for k, v in extra_dct.items():
            openurl += '&%s=%s' % ( urllib.parse.quote_plus(k), urllib.parse.quote_plus(v) )
        # illiad_url = settings_app.ILLIAD_URL_ROOT % openurl  # ILLIAD_URL_ROOT is like `http...OpenURL?%s
        illiad_url = openurl
        log.debug( 'illiad_url, ```%s```' % illiad_url )
        return illiad_url

    def check_identifiers( self, ill_bib_dct ):
        """ Gets oclc or pubmed IDs.
            Called by make_illiad_url() """
        extra_dct = {}
        identifiers = ill_bib_dct.get( 'identifier', [] )
        for idt in identifiers:
            if idt['type'] == 'pmid':
                extra_dct['Notes'] = '`PMID: {}`'.format( idt['id'] )
                # extra_dct['Notes'] = self.update_note( 'foo', 'bar' )
            elif idt['type'] == 'oclc':
                extra_dct['ESPNumber'] = idt['id']
        log.debug( f'extra_dct, ```{extra_dct}```' )
        return extra_dct

    def check_validity( self, ill_bib_dct, extra_dct ):
        """ Updates notes if necessary based on IlliadValidator.add_required_kvs() work.
            Called by make_illiad_url() """
        if ill_bib_dct.get('_valid') is not True:
            if extra_dct.get('Notes') is None:
                extra_dct['Notes'] = ''
            # extra_dct['Notes'] += '\rNot enough data provided by original request.'
            extra_dct['Notes'] = self.update_note( extra_dct['Notes'], '`not enough original-request data`' )
        log.debug( f'extra_dct, ```{extra_dct}```' )
        return extra_dct

    def enhance_citation( self, ill_bib_dct, original_querystring ):
        """ Enhances low-quality bib-dct data from original_querystring-data when possible.
            Called by: make_illiad_url() """
        original_bib_dct = ill_bib_dct.copy()
        log.debug( f'ill_bib_dct, ```{pprint.pformat(ill_bib_dct)}```' )
        log.debug( f'original_querystring, ```{original_querystring}```' )
        param_dct = parse_qs( original_querystring )
        log.debug( f'param_dct, ```{pprint.pformat(param_dct)}```' )
        if ill_bib_dct['type'] == 'article':
            if 'author' not in ill_bib_dct.keys():
                if 'rft.creator' in param_dct.keys():
                    auth_string = ', '.join( param_dct['rft.creator'] )
                    ill_bib_dct['author'] = [ {'name': f'(?) {auth_string}'} ]
            if 'title' not in ill_bib_dct.keys() or ill_bib_dct.get( 'title', '' ).lower() == 'unknown':
                if 'rft.source' in param_dct.keys():
                    atitle_string = ', '.join( param_dct['rft.source'] )
                    ill_bib_dct['title'] = f'(?) {atitle_string}'
            found_issn = False
            found_isbn_str = None
            if 'identifier' in ill_bib_dct.keys():
                log.debug( 'hereA' )
                id_dct_lst = ill_bib_dct['identifier']
                for id_dct in id_dct_lst:
                    log.debug( f'id_dct, ```{id_dct}```' )
                    if 'type' in id_dct.keys():
                        if id_dct['type'] == 'issn':
                            found_issn = True
                            break
                        elif id_dct['type'] == 'isbn':
                            log.debug( 'hereB' )
                            found_isbn_str = id_dct['id']
                log.debug( f'found_issn, `{found_issn}`; found_isbn_str, `{found_isbn_str}`' )
                if found_issn is False and found_isbn_str is not None:
                    ill_bib_dct['identifier'].append( {'type': 'issn', 'id': f'(?)_{found_isbn_str}' } )
        misc.diff_dicts( original_bib_dct, 'original_bib_dct', ill_bib_dct, 'modified_dct' )  # just logs diffs
        return ill_bib_dct

    # def enhance_citation( self, ill_bib_dct, original_querystring ):
    #     """ Enhances low-quality bib-dct data from original_querystring-data when possible.
    #         Called by: make_illiad_url() """
    #     original_bib_dct = ill_bib_dct.copy()
    #     log.debug( f'ill_bib_dct, ```{pprint.pformat(ill_bib_dct)}```' )
    #     log.debug( f'original_querystring, ```{original_querystring}```' )
    #     param_dct = parse_qs( original_querystring )
    #     log.debug( f'param_dct, ```{pprint.pformat(param_dct)}```' )
    #     if ill_bib_dct['type'] == 'article':
    #         if 'author' not in ill_bib_dct.keys():
    #             if 'rft.creator' in param_dct.keys():
    #                 auth_string = ', '.join( param_dct['rft.creator'] )
    #                 ill_bib_dct['author'] = [ {'name': f'(?) {auth_string}'} ]
    #         if 'title' not in ill_bib_dct.keys() or ill_bib_dct.get( 'title', '' ).lower() == 'unknown':
    #             if 'rft.source' in param_dct.keys():
    #                 atitle_string = ', '.join( param_dct['rft.source'] )
    #                 ill_bib_dct['title'] = f'(?) {atitle_string}'
    #     misc.diff_dicts( original_bib_dct, 'original_bib_dct', ill_bib_dct, 'modified_dct' )  # just logs diffs
    #     return ill_bib_dct

    def update_note( self, initial_note, additional_note ):
        """ Updates notes with correct spacing & punctuation.
            Called by check_identifiers(), check_validity(), make_illiad_url() """
        log.debug( 'starting update_note' )
        note = initial_note
        if note is None:
            note = additional_note
        elif len( note.strip() ) == 0:
            note = additional_note
        else:
            note += '; {}'.format( additional_note )
        log.debug( 'note now, ```{}```'.format(note) )
        return note

    # end class IlliadUrlBuilder


class IlliadValidator( object ):
    """ Adds required keys and values for illiad.
        Also returns a 'validity' check to indicate to the url-builder whether the supplied information is complete.
            If the validity-check is false, the url-builder will add a note that there was not enough information supplied.
        Called by IlliadHelper.make_illiad_url() """

    # def add_required_kvs( self, bib_dct ):
    #     """ Adds required keys and values for illiad.
    #         Called by IlliadHelper.make_illiad_url() """
    #     original_bib_dct = bib_dct.copy()
    #     valid_check = True
    #     if bib_dct['type'] == 'article':
    #         ( bib_dct, valid_check ) = self._handle_article( bib_dct, valid_check )
    #     elif bib_dct['type'] == 'book':
    #         ( bib_dct, valid_check ) = self._handle_book( bib_dct, valid_check )
    #     elif (bib_dct['type'] == 'bookitem') or (bib_dct['type'] == 'inbook'):  # TL: These should all be inbooks but checking for now.
    #         ( bib_dct, valid_check ) = self._handle_bookish( bib_dct, valid_check )
    #     bib_dct['_valid'] = valid_check
    #     # log.debug( f'modifed_bib_dct, ```{pprint.pformat(bib_dct)}```' )
    #     misc.diff_dicts( original_bib_dct, 'original_bib_dct', bib_dct, 'modified_dct' )  # just logs diffs
    #     return bib_dct

    def add_required_kvs( self, bib_dct ):
        """ Adds required keys and values for illiad.
            Called by IlliadHelper.make_illiad_url() """
        original_bib_dct = bib_dct.copy()
        valid_check = True
        if bib_dct['type'] == 'article':
            ( bib_dct, valid_check ) = self._handle_article( bib_dct, valid_check )
        elif bib_dct['type'] == 'book':
            ( bib_dct, valid_check ) = self._examine_book( bib_dct, valid_check )
        elif (bib_dct['type'] == 'bookitem') or (bib_dct['type'] == 'inbook'):  # TL: These should all be inbooks but checking for now.
            ( bib_dct, valid_check ) = self._handle_bookish( bib_dct, valid_check )
        bib_dct['_valid'] = valid_check
        misc.diff_dicts( original_bib_dct, 'original_bib_dct', bib_dct, 'modified_dct' )  # just logs diffs
        return bib_dct

    def _handle_article( self, bib_dct, valid_check ):
        """ Updates bib_dct with article values.
            Called by add_required_kvs() """
        if bib_dct.get('journal') is None:
            bib_dct['journal'] = {'name': 'Not provided'}; valid_check = False
        if bib_dct.get('year') is None:
            bib_dct['year'] = '?'; valid_check = False
        if bib_dct.get('title') is None:
            bib_dct['title'] = 'Title not specified'; valid_check = False
        if bib_dct.get('pages') is None:
            bib_dct['pages'] = '? - ?'; valid_check = False
        return ( bib_dct, valid_check )

    def _examine_book( self, bib_dct, valid_check ):
        """ Updates bib_dct genre if necessary.
            Called by add_required_kvs() """
        log.debug( 'here' )
        handle_book_flag = True
        if bib_dct.get( 'identifier', None ):
            for element_dct in bib_dct['identifier']:
                if 'type' in element_dct.keys():
                    if element_dct['type'] == 'pmid':
                        bib_dct['type'] = 'article'
                        handle_book_flag = False
                        ( bib_dct, valid_check ) = self._handle_article( bib_dct, valid_check )
        if handle_book_flag is True:
            ( bib_dct, valid_check ) = self._handle_book( bib_dct, valid_check )
        return ( bib_dct, valid_check )

    def _handle_book( self, bib_dct, valid_check ):
        """ Updates bib_dct with book values.
            Called by add_required_kvs() """
        if bib_dct.get('title') is None:
            bib_dct['title'] = 'Not available'
            valid_check = False
        return ( bib_dct, valid_check )

    def _handle_bookish( self, bib_dct, valid_check ):
        """ Updates bib_dct with bookitem or inbook values.
            Called by add_required_kvs() """
        if bib_dct.get('title') is None:
            bib_dct['title'] = 'Title not specified'; valid_check = False
        if bib_dct.get('journal') is None:
            bib_dct['journal'] = {'name': 'Source not provided'}; valid_check = False
        pages = bib_dct.get('pages')
        if (pages == []) or (pages is None):
            bib_dct['pages'] = '? - ?'; valid_check = False
        return ( bib_dct, valid_check )

    # end class IlliadValidator


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
            # 'openurl': self.grab_openurl_from_illiad_full_url( illiad_full_url ),  # required
            'openurl': illiad_full_url,  # required
            'patron_barcode': usr_dct['patron_barcode'],
            'patron_department': '',
            'patron_status': '',
            'phone': '',
            # 'volumes': '',
        }
        log.debug( '`%s` - submission param_dct prepared, ```%s```' % (self.log_id, pprint.pformat(param_dct)) )
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
