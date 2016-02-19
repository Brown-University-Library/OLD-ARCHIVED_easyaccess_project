# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint, re, urlparse

from delivery.models import Resource
from django.core.urlresolvers import reverse
from shorturls import baseconv


log = logging.getLogger('access')


class Permalink( object ):
    """ Handles creation of permalinks from views.findit_base_resolver(),
        and lookup from incoming permalinks from views.permalink() """

    def make_permalink( self, referrer, qstring, scheme, host, path ):
        """ Creates a delivery.models.Resource entry if one doesn't exist, and creates and returns a permalink string.
            Called by views.base_resolver() """
        resource_id = self._get_resource( qstring, referrer )
        permastring = baseconv.base62.from_decimal( resource_id )
        permalink = '%s://%s%spermalink/%s/' % ( scheme, host, path, permastring )
        return_dct = { 'permalink': permalink, 'querystring': qstring, 'referrer': referrer, 'resource_id': resource_id, 'permastring': permastring  }
        log.debug( 'return_dct, ```%s```' % pprint.pformat(return_dct) )
        return return_dct

    def _get_resource( self, qstring, referrer ):
        """ Gets or creates resource entry and returns id.
            Called by make_permalink() """
        try:
            rsc = Resource.objects.get( query=qstring, referrer=referrer )
            log.debug( 'rsc found' )
        except:
            log.debug( 'rsc not found' )
            rsc = Resource()
            rsc.query = qstring
            rsc.referrer = referrer
            rsc.save()
        log.debug( 'rsc.__dict__, ```%s```' % pprint.pformat(rsc.__dict__) )
        return rsc.id

    def get_openurl( self, permalink_str ):
        """ Retreives querystring for given permalink_str.
            Called by views.permalink() """
        record_id = permastring = baseconv.base62.to_decimal( permalink_str )
        try:
            rsc = Resource.objects.get( id=record_id )
            qstring = rsc.query
            log.debug( 'rsc found' )
        except:
            log.debug( 'rsc not found' )
            qstring = None
        log.debug( 'qstring, ```%s```' % pprint.pformat(qstring) )
        return qstring

    # end class Permalink()
