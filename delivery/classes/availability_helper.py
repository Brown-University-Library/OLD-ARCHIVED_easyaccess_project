# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
import bibjsontools
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

    # end class AvailabilityViewHelper()


#===============================================================================
# Manages josiah-availability.
# Checks availability & updates ezb db if necessary.
#===============================================================================
class JosiahAvailabilityManager(object):

    def __init__(self):
        self.available = False  # set by check_josiah_availability(); used by views.ResolveView.get()
        self.search_dict = {}  # set by check_josiah_availability(); used by update_ezb_availability()
        log.debug( 'availability_checker instantiated' )

    def check_josiah_availability( self, bibj ):
        """Checks josiah availability for books."""
        ## worth checking? (don't if not a book, or no good identifiers)
        worth_checking = False
        if bibj[u'type'] == u'book':
            search_dict = { u'isbn': u'', u'oclc': u'' }
            for entry in bibj[u'identifier']:
                if entry[u'type'] == u'isbn':
                    search_dict[u'isbn'] = entry[u'id']
                elif entry[u'type'] == u'oclc':
                    search_dict[u'oclc'] = entry[u'id']
            if search_dict[u'isbn'] or search_dict[u'oclc']:
                worth_checking = True
                self.search_dict = search_dict
        alog.debug( u'in JosAvManager.check_josiah_availability(); worth_checking: %s' % worth_checking )
        ## the check
        if worth_checking:
            url_base = u'http://library.brown.edu/services/availability'
            for key,value in search_dict.items():
                url = u'%s/%s/%s/' % ( url_base, key, value )
                alog.debug( u'in JosAvManager.check_josiah_availability(); url to try: %s' % url )
                availability_dict = { u'items': [] }
                try:
                    r = requests.get( url, timeout=5 )
                    availability_dict = json.loads( r.content.decode(u'utf-8', u'replace') )
                    alog.debug( u'in JosAvManager.check_josiah_availability(); availability_dict: %s' % pprint.pformat(availability_dict) )
                except Exception as e:
                    alog.error( u'in JosAvManager.check_josiah_availability(); exception: %s' % repr(e).decode(u'utf-8', u'replace') )
                for item in availability_dict[u'items']:
                    if item[u'is_available'] == True:
                        self.available = u'via_%s' % key.lower()
                        break
                if self.available:
                    break
        alog.debug( u'in JosAvManager.check_josiah_availability(); self.available: %s' % self.available )
        return

    def update_ezb_availability( self, bibj ):
        """Updates ezborrow requests table if item is available."""
        from django.core.cache import cache
        from easyborrow_models import EasyBorrowRequest
        assert self.available  # set in check_josiah_availability()
        alog.debug( u'in JosAvManager.update_ezb_availability(); self.search_dict: %s' % pprint.pformat(self.search_dict) )
        ## really update? (don't if a recent entry was added)
        do_update = False
        if cache.get( unicode(self.search_dict) ):  # key is unicode(dict); value doesn't matter
            alog.debug( u'in JosAvManager.update_ezb_availability(); cache found' )
            pass
        else:
            do_update = True
            cache.set( unicode(self.search_dict), u'last_set: %s' % datetime.now(), 60*60 )  # 1 hour; set value doesn't matter
            alog.debug( u'in JosAvManager.update_ezb_availability(); cache set with value, %s' % cache.get(unicode(self.search_dict)) )
        ## the update
        if do_update:
            try:
                req = EasyBorrowRequest(
                    created=datetime.now(),
                    title=bibj[u'title'],
                    isbn=self.search_dict[u'isbn'],
                    wc_accession=self.search_dict[u'oclc'],
                    request_status=u'in_josiah_%s' % self.available,
                    volumes=u'', sfxurl=u'', eppn=u'', name=u'', firstname=u'', lastname=u'', barcode=u'', email=u'' )
                req.save( using=u'ezborrow' )
                alog.debug( u'in JosAvManager.update_ezb_availability(); ezb db updated' )
            except Exception as e:
                alog.error( u'in JosAvManager.update_ezb_availability(); exception updating ezb table: %s' % repr(e).decode(u'utf-8', u'replace') )
        return

    # end class JosiahAvailabilityManager()
