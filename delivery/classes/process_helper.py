# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, logging
from delivery.easyborrow_models import EasyBorrowRequest
from django.core.urlresolvers import reverse


log = logging.getLogger('access')


class ProcessViewHelper(object):
    """ Contains helpers for views.process_request() """

    def __init__(self):
        pass

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /availability/.
            Called by views.login() """
        ( referrer_check, redirect_url, last_path ) = ( False, '', session_dct.get('last_path', '') )
        if last_path == '/easyaccess/borrow/login/':
            referrer_check = True
        if referrer_check is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('delivery:message_url'), querystring=meta_dct.get('QUERYSTRING', '') )
        log.debug( 'referrer_check, `{referrer_check}`; redirect_url, ```{redirect_url}```'.format(referrer_check=referrer_check, redirect_url=redirect_url) )
        return ( referrer_check, redirect_url )

    def save_to_easyborrow( self, session_dct ):
        """ Creates an easyBorrow db entry.
            Called by views.process_request() """
        log.debug( 'starting' )

        ezb_rqst = EasyBorrowRequest()

        ezb_rqst.title = 'foo'
        ezb_rqst.isbn = 'foo'
        ezb_rqst.wc_accession = 123
        ezb_rqst.bibno = 'foo'
        ezb_rqst.pref = 'foo'
        ezb_rqst.loc = 'foo'
        ezb_rqst.alt_edition = 'foo'
        ezb_rqst.volumes = 'foo'
        ezb_rqst.sfxurl = 'long foo'
        ezb_rqst.patronid = 123
        ezb_rqst.eppn = 'foo'
        ezb_rqst.name = 'foo'
        ezb_rqst.firstname = 'foo'
        ezb_rqst.lastname = 'foo'
        ezb_rqst.created = datetime.datetime.now()
        ezb_rqst.barcode = 'foo'
        ezb_rqst.email = 'foo'
        ezb_rqst.group = 'foo'
        ezb_rqst.staffnote = 'foo'
        ezb_rqst.request_status = 'foo'

        ezb_rqst.save()
        log.debug( 'ezb_rqst.id, `{}`'.format(ezb_rqst.id) )

        return

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
