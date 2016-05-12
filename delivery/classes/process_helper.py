# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, logging, pprint, time
from delivery import app_settings
from delivery.easyborrow_models import EasyBorrowRequest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote


log = logging.getLogger('access')


class ProcessViewHelper(object):
    """ Contains helpers for views.process_request() """

    def __init__(self):
        pass

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /availability/.
            Called by views.login() """
        log.debug( 'meta_dct, ```{}```'.format(pprint.pformat(meta_dct)) )
        ( referrer_check, redirect_url, last_path ) = ( False, '', session_dct.get('last_path', '') )
        if last_path == '/easyaccess/borrow/login/':
            referrer_check = True
        if referrer_check is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_check, `{referrer_check}`; redirect_url, ```{redirect_url}```'.format(referrer_check=referrer_check, redirect_url=redirect_url) )
        return ( referrer_check, redirect_url )

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
            log.error( 'exception creating patron_dct, ```{}```'.format(unicode(repr(e))) )
        log.debug( 'patron_dct, ```{}```'.format(pprint.pformat(patron_dct)) )
        return patron_dct

    def _make_item_dct( self, bib_dct, querystring ):
        """ Maps item info to db info.
            Called by save_to_easyborrow() """
        try: oclc_num = int( bib_dct.get('oclc_num', '') )
        except: oclc_num = 0
        item_dct = {
            'title': bib_dct.get( 'title', ''),
            'isbn': bib_dct.get( 'isbn', ''),
            'wc_accession': oclc_num,
            'sfxurl': querystring,
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
            ezb_rqst.created = datetime.datetime.now()
            return ezb_rqst
        except Exception as e:
            log.error( 'exception ezb record, ```{}```'.format(unicode(repr(e))) )
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

    def build_shiblogout_redirect_url( self, request ):
        """ If localhost, just returns the message_url,
            otherwise builds the shib-logout url with a _full_ message_url included.
            Called by views.process_request() """
        redirect_url = reverse( 'delivery:message_url' )
        if not ( request.get_host() == '127.0.0.1' and settings.DEBUG2 == True ):  # eases local development
            redirect_url = 'https://{host}{message_url}'.format( host=request.get_host(), message_url=reverse('delivery:message_url') )
            encoded_redirect_url = urlquote( redirect_url )  # django's urlquote()
            redirect_url = '%s?return=%s' % ( app_settings.SHIB_LOGOUT_URL_ROOT, encoded_redirect_url )
        log.debug( 'redirect_url, ```{}```'.format(redirect_url) )
        return redirect_url

    # end class ProcessViewHelper()






# def prep_book_request(request):
#     """
#     Map the incoming bibjson object to the ezborrow request.
#     """
#     from easyborrow_models import EasyBorrowRequest
#     from datetime import datetime
#     bib = request.bib
#     user = request.user
#     #Helper to pull out first ID of a given type.
#     def _first_id(id_type):
#         try:
#             return [id['id'] for id in bib.get('identifier', []) if id['type'] == id_type][0]
#         except IndexError:
#             return ''
#             if id_type == 'isbn':
#                 return ''
#             else:
#                 return None
#     #import pdb; pdb.set_trace();
#     #Register the user with illiad if necessary.
#     registration = illiad_client(request)
#     req = EasyBorrowRequest()
#     req.created = datetime.now()
#     req.title = bib.get('title')
#     isbn = _first_id('isbn')
#     if isbn is not None:
#         req.isbn = isbn.replace('-', '').strip()
#     try:
#         oclc = int(_first_id('oclc'))
#         req.wc_accession = oclc
#     except (TypeError, ValueError):
#         pass
#     req.volumes = bib.get('_volume_note', '')
#     #This sersol url is required at the moment for the controller code.
#     req.sfxurl = 'http://%s.search.serialssolutions.com/?%s' % ( os.environ['EZACS__BUL_LINK_SERSOL_KEY'], bib.get('_query') )
#     req.eppn = user.username.replace('@brown.edu', '')
#     req.name = "%s %s" % (user.first_name, user.last_name)
#     req.firstname = user.first_name
#     req.lastname = user.last_name
#     #Pull barcode from profile.
#     profile = user.libraryprofile
#     req.barcode = profile.barcode
#     req.email = user.email
#     #import pdb; pdb.set_trace();
#     req.save(using='ezborrow')
#     #This is a workaround to return the id of the object created above.
#     #Since this is an existing database, I would prefer just to hit the db
#     #again and get this users latest request id rather than try to alter the
#     #schema to make it return an id.
#     #This causes a second hit to the database to fetch the id of the item just requested.
#     latest = EasyBorrowRequest.objects.using('ezborrow').filter(email=user.email).order_by('-created')[0]
#     return {'transaction_number': latest.id}
