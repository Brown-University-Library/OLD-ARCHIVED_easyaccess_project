# -*- coding: utf-8 -*-

import logging
from article_request_app import settings_app
from django.utils.http import urlencode, urlquote


log = logging.getLogger('access')


class ShibLoginHelper( object ):
    """ Contains helpers for views.login_handler() """

    # def build_shib_sp_querystring( self, url_path, citation_json, format, illiad_url, querystring, log_id ):
    # def build_shib_sp_querystring( self, url_path, shortkey, citation_json, format, illiad_url, querystring, log_id ):
    def build_shib_sp_querystring( self, url_path, shortkey, citation_json, format, querystring, log_id ):
        """ Builds querystring for redirect to shib SP url, which will redirect back to views.login_handler().
            Called by views.shib_login() """
        # self.check_params( [ citation_json, format, illiad_url, querystring, log_id ] )
        self.check_params( [ shortkey, citation_json, format, querystring, log_id ] )
        # segment = '{path}?citation_json={ctn_jsn}&format={fmt}&illiad_url={ill_url}&querystring={qs}&ezlogid={id}'.format(
        #     path=url_path,
        #     ctn_jsn=urlquote( citation_json ),
        #     fmt=urlquote( format ),
        #     ill_url=urlquote( illiad_url ),
        #     qs=urlquote( querystring ),
        #     id=log_id )
        segment = '{path}?shortkey={shortkey}&citation_json={ctn_jsn}&format={fmt}&querystring={qs}&ezlogid={id}'.format(
            path=url_path,
            shortkey=shortkey,
            ctn_jsn=urlquote( citation_json ),
            fmt=urlquote( format ),
            # ill_url=urlquote( illiad_url ),
            qs=urlquote( querystring ),
            id=log_id )
        log.debug( f'segment, ```{segment}```' )
        querystring = urlencode( {'target': segment} )  # yields 'target=(encoded-segment)'
        assert type(querystring) == str, type(querystring)
        log.debug( 'querystring for redirect to shib SP login url, ```%s```' % querystring )
        return querystring

    # def build_localdev_querystring( self, citation_json, format, illiad_url, querystring, log_id ):
    def build_localdev_querystring( self, shortkey, citation_json, format, querystring, log_id ):
        """ Builds querystring for redirect right to views.login_handler()
            Called by views.shib_login()
            TODO: I think the only param should be the short-key, with everything else saved, and later retrieved from the bul_link_db. """
        self.check_params( [ shortkey, citation_json, format, querystring, log_id ] )
        # querystring = 'citation_json={ctn_jsn}&format={fmt}&illiad_url={ill_url}&querystring={qs}&ezlogid={id}'.format(
        #     ctn_jsn=urlquote(citation_json),
        #     fmt=urlquote(format),
        #     ill_url=urlquote(illiad_url),
        #     qs=urlquote(querystring),
        #     id=log_id )
        querystring = 'shortkey={shortkey}&citation_json={ctn_jsn}&format={fmt}&querystring={qs}&ezlogid={id}'.format(
            shortkey=shortkey,
            ctn_jsn=urlquote(citation_json),
            fmt=urlquote(format),
            # ill_url=urlquote(illiad_url),
            qs=urlquote(querystring),
            id=log_id )
        assert type(querystring) == str, type(querystring)
        log.debug( 'querystring for localdev redirect to views.login_handler(), ```%s```' % querystring )
        return querystring

    def check_params(self, params_list ):
        """ Checks that params are unicode-strings.
            Called by build_localdev_querystring() and build_shib_sp_querystring() """
        for param in params_list:
            assert type(param) == str, type(param)
        return

    ## end class ShibLoginHelper()
