# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
from django.utils.http import urlencode, urlquote


log = logging.getLogger('access')


class ShibLoginHelper( object ):
    """ Contains helpers for views.login_handler() """

    def build_shib_sp_querystring( self, bib_dct_json, last_querystring, shortlink_url, log_id ):
        """ Builds querystring for redirect to shib SP url, which will redirect back to views.login_handler().
            Called by views.shib_login() """
        self.check_params( [ bib_dct_json, last_querystring, shortlink_url, log_id ] )
        segment = '/easyaccess/borrow/login_handler/?bib_dct_json={bib_jsn}&last_querystring={qs}&permalink_url={shrtlnk}&ezlogid={id}'.format(
            bib_jsn=urlquote( bib_dct_json ),
            qs=urlquote( last_querystring ),
            shrtlnk=urlquote( shortlink_url ),
            id=log_id )
        querystring = urlencode( {'target': segment} ).decode( 'utf-8' )  # yields 'target=(encoded-segment)'
        assert type(querystring) == unicode, type(querystring)
        log.debug( 'querystring for redirect to shib SP login url, ```%s```' % querystring )
        return querystring

    def build_localdev_querystring( self, bib_dct_json, last_querystring, shortlink_url, log_id ):
        """ Builds querystring for redirect right to views.login_handler()
            Called by views.shib_login() """
        self.check_params( [ bib_dct_json, last_querystring, shortlink_url, log_id ] )
        querystring = 'bib_dct_json={bib_jsn}&last_querystring={qs}&permalink_url={shrtlnk}&ezlogid={id}'.format(
            bib_jsn=urlquote( bib_dct_json ),
            qs=urlquote( last_querystring ),
            shrtlnk=urlquote( shortlink_url ),
            id=log_id )
        assert type(querystring) == unicode, type(querystring)
        log.debug( 'querystring for localdev redirect to views.login_handler(), ```%s```' % querystring )
        return querystring

    def check_params(self, params_list ):
        """ Checks that params are unicode-strings.
            Called by build_localdev_querystring() and build_shib_sp_querystring() """
        for param in params_list:
            assert type(param) == unicode, type(param)
        return

    ## end class ShibLoginHelper()
