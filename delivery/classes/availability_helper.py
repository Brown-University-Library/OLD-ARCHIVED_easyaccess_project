# -*- coding: utf-8 -*-

from __future__ import unicode_literals


#===============================================================================
# Manages josiah-availability.
# Checks availability & updates ezb db if necessary.
#===============================================================================
class JosiahAvailabilityManager(object):

    def __init__(self):
        self.available = False  # set by check_josiah_availability(); used by views.ResolveView.get()
        self.search_dict = {}  # set by check_josiah_availability(); used by update_ezb_availability()

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
