# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, logging, pprint, time
from delivery import app_settings
from delivery.easyborrow_models import EasyBorrowRequest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.http import urlquote


log = logging.getLogger('access')


class ProcessViewHelper(object):
    """ Contains helpers for delivery.views.process_request() """

    def __init__( self, log_id='not_set' ):
        self.log_id = log_id
        self.denied_permission_message = '''
It appears you are not authorized to use interlibrary-loan services, which are for the use of faculty, staff, and students.

If you believe you should be permitted to use interlibrary-loan services, please contact the circulation staff at the Rockefeller Library, or call them at {phone}, or email them at {email}, and they'll help you.
'''.format( phone=app_settings.PERMISSION_DENIED_PHONE, email=app_settings.PERMISSION_DENIED_EMAIL )

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /availability/.
            Called by delivery.views.process_request() """
        log.debug( 'meta_dct before referrer_check, ```{}```'.format(pprint.pformat(meta_dct)) )
        log.debug( 'session_dct.items() before referrer_check, ```{}```'.format(pprint.pformat(session_dct.items())) )
        ( referrer_check, redirect_url, last_path ) = ( False, '', session_dct.get('last_path', '') )
        if '/borrow/login_handler/' in last_path:
            referrer_check = True
        if referrer_check is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_check, `{referrer_check}`; redirect_url, ```{redirect_url}```'.format(referrer_check=referrer_check, redirect_url=redirect_url) )
        return ( referrer_check, redirect_url )

    def check_if_authorized( self, shib_dct ):
        """ Checks whether user is authorized to request book.
            Called by views.process_request() """
        log.debug( '`{id}` checking authorization'.format(id=self.log_id) )
        ( is_authorized, redirect_url, message ) = ( False, reverse('delivery:shib_logout_url'), self.denied_permission_message )
        if app_settings.REQUIRED_GROUPER_GROUP in shib_dct.get( 'member_of', '' ):
            log.debug( '`{id}` user authorized'.format(id=self.log_id) )
            ( is_authorized, redirect_url, message ) = ( True, '', '' )
        log.debug( '`{id}` is_authorized, `{auth}`; redirect_url, `{url}`; message, ```{msg}```'.format(id=self.log_id, auth=is_authorized, url=redirect_url, msg=message) )
        return ( is_authorized, redirect_url, message )

    def save_to_easyborrow( self, shib_dct, bib_dct, querystring ):
        """ Creates an easyBorrow db entry.
            Called by views.process_request() """
        patron_dct = self._make_patron_dct( shib_dct )
        item_dct = self._make_item_dct( bib_dct, querystring )
        ezb_rqst = self._make_record( patron_dct, item_dct )
        if ezb_rqst:
            ezb_rqst.save( using='ezborrow' )
            ezb_db_id = '{}'.format( ezb_rqst.pk )
            log.debug( 'ezb_db_id, `{}`'.format(ezb_db_id) )
            return ezb_db_id
        else:
            return None

    def _make_patron_dct( self, shib_dct ):
        """ Maps shib info to db info.
            Called by save_to_easyborrow() """
        log.debug( f'shib_dct, ```{pprint.pformat(shib_dct)}```' )
        patron_dct = {}
        try:
            patron_dct = {
                'patronid': 0,
                'eppn': shib_dct['id_short'],  # NB: not really eppn (no @brown.edu)
                'name': '{first} {last}'.format( first=shib_dct['name_first'], last=shib_dct['name_last'] ),
                'firstname': shib_dct['name_first'],
                'lastname': shib_dct['name_last'],
                'barcode': shib_dct['patron_barcode'],
                'email': shib_dct['email'],
                'group': shib_dct['brown_type'] }  # NB: could be shib_dct['edu_person_primary_affiliation']
        except Exception as e:
            # log.error( 'exception creating patron_dct, ```{}```'.format(unicode(repr(e))) )  # py2
            log.exception( 'exception creating patron_dct; will show traceback, but continue and return `{}`' )
        log.debug( f'patron_dct, ```{pprint.pformat(patron_dct)}```' )
        return patron_dct

    # def _make_item_dct( self, bib_dct, querystring ):
    #     """ Maps item info to db info.
    #         Called by save_to_easyborrow() """
    #     try: oclc_num = int( bib_dct.get('oclc_num', '') )
    #     except: oclc_num = 0
    #     item_dct = {
    #         'title': bib_dct.get( 'title', '' ),
    #         'isbn': bib_dct.get( 'isbn', '').replace( '-', '' ),
    #         'wc_accession': oclc_num,
    #         'sfxurl': 'http://{ss_key}.search.serialssolutions.com/?{querystring}'.format( ss_key=app_settings.SERSOL_KEY, querystring=querystring ),
    #         'volumes': bib_dct.get( 'easyborrow_volumes', '' ) }
    #     log.debug( 'item_dct, ```{}```'.format(pprint.pformat(item_dct)) )
    #     return item_dct

    def _make_item_dct( self, bib_dct, querystring ):
        """ Maps item info to db info.
            Called by save_to_easyborrow() """
        try: oclc_num = int( bib_dct.get('oclc_num', '') )
        except: oclc_num = 0
        item_dct = {
            'title': bib_dct.get( 'title', '' )[0:254],
            'isbn': bib_dct.get( 'isbn', '').replace( '-', '' ),
            'wc_accession': oclc_num,
            'sfxurl': 'http://{ss_key}.search.serialssolutions.com/?{querystring}'.format( ss_key=app_settings.SERSOL_KEY, querystring=querystring ),
            'volumes': bib_dct.get( 'easyborrow_volumes', '' ) }
        log.debug( 'item_dct, ```{}```'.format(pprint.pformat(item_dct)) )
        return item_dct

    def _make_record( self, patron_dct, item_dct ):
        """ Populates ezb-request instance.
            Called by save_to_easyborrow() """
        try:
            ezb_rqst = EasyBorrowRequest()
            ## patron
            ezb_rqst.patronid = patron_dct['patronid']
            ezb_rqst.eppn = patron_dct['eppn']
            ezb_rqst.name = patron_dct['name']
            ezb_rqst.firstname = patron_dct['firstname']
            ezb_rqst.lastname = patron_dct['lastname']
            ezb_rqst.barcode = patron_dct['barcode']
            ezb_rqst.email = patron_dct['email']
            ezb_rqst.group = patron_dct['group']
            ## item
            ezb_rqst.title = item_dct['title']
            ezb_rqst.isbn = item_dct['isbn']
            ezb_rqst.wc_accession = item_dct['wc_accession']
            ezb_rqst.bibno = ''
            ezb_rqst.sfxurl = item_dct['sfxurl']
            ## item-special (from landing page)
            ezb_rqst.volumes = item_dct['volumes']
            ## request-meta-default
            ezb_rqst.pref = 'quick'
            ezb_rqst.loc = 'rock'
            ezb_rqst.alt_edition = 'y'
            ezb_rqst.request_status = 'not_yet_processed'
            ezb_rqst.staffnote = ''
            ## request-meta-dynamic
            # ezb_rqst.created = datetime.datetime.now()
            ezb_rqst.created = timezone.now()  # if settings.USE_TZ were True, would automatically create proper UTC time
            log.debug( 'ezb_rqst.created, ```%s```' % unicode(ezb_rqst.created) )
            return ezb_rqst
        except Exception as e:
            # log.error( 'exception ezb record, ```{}```'.format(unicode(repr(e))) )  # py2
            log.exception( 'error populating the ezb-request instance; will show traceback, but continue and return `None`.' )
            return None

    def build_submitted_message( self, firstname, lastname, bib_dct, ezb_db_id, email ):
        """ Prepares submitted message
            Called by views.process_request() """
        if bib_dct.get( 'title', '' ) != '':
            title = bib_dct['title']
        else:
            title = bib_dct['source']
        message = '''
Greetings {firstname} {lastname},

We're getting the title '{title}' for you. You'll soon receive more information in an email.

Some information for your records:

- Title: '{title}'
- Your easyBorrow reference number: '{ezb_reference_num}'
- Notification of arrival will be sent to email address: <{email}>

If you have any questions, contact the Library's Interlibrary Loan office at <interlibrary_loan@brown.edu> or call 401-863-2169.

  '''.format(
        firstname=firstname,
        lastname=lastname,
        title=title,
        ezb_reference_num=ezb_db_id,
        email=email )
        log.debug( 'ezb submitted message built' )
        return message

    ## end class ProcessViewHelper()
