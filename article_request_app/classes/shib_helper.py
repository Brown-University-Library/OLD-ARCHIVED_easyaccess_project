# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
from django.utils.http import urlquote


log = logging.getLogger('access')


class ShibLoginHelper( object ):
    """ Contains helpers for views.login_handler() """

    def build_localdev_querystring( self, citation_json, format, illiad_url, querystring, log_id ):
        """ Builds querystring for redirect right to views.login_handler()
            Called by views.shib_login() """
        assert type(citation_json) == unicode, type(citation_json)
        assert type(format) == unicode, type(format)
        assert type(illiad_url) == unicode, type(illiad_url)
        assert type(querystring) == unicode, type(querystring)
        assert type(log_id) == unicode, type(log_id)
        querystring = 'citation_json={ctn_jsn}&format={fmt}&illiad_url={ill_url}&querystring={qs}&ezlogid={id}'.format(
            ctn_jsn=urlquote(citation_json),
            fmt=urlquote(format),
            ill_url=urlquote(illiad_url),
            qs=urlquote(querystring),
            id=log_id
            )
        log.debug( 'querystring for localdev redirect to views.login_handler(), ```%s```' % querystring )
        return querystring
