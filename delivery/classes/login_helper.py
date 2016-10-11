# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, logging, pprint
from common_classes.shib_helper import ShibChecker
from delivery import app_settings as settings_app
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote


log = logging.getLogger('access')
shib_checker = ShibChecker()


class LoginViewHelper(object):
    """ Contains helpers for views.login_handler() """

    def __init__(self):
        pass

    def check_referrer( self, session_dct, meta_dct ):
        """ Ensures request came from /availability/.
            Called by views.login_handler() """
        ( referrer_ok, redirect_url, last_path, shib_status ) = ( False, '', session_dct.get('last_path', ''), session_dct.get('shib_status', '') )
        log.debug( 'last_path, `{}`'.format(session_dct.get('last_path', '')) )
        if last_path == '/easyaccess/borrow/availability/':
            referrer_ok = True
        if referrer_ok is False:
            redirect_url = '{findit_url}?{querystring}'.format( findit_url=reverse('findit:findit_base_resolver_url'), querystring=meta_dct.get('QUERY_STRING', '') )
        log.debug( 'referrer_ok, `{referrer_ok}`; redirect_url, ```{redirect_url}```'.format(referrer_ok=referrer_ok, redirect_url=redirect_url) )
        return ( referrer_ok, redirect_url )

    def check_querystring( self, querystring ):
        """ Handles situation where querystring is truncated in the middle of character-encoding,
              leaving a badly-formed openurl which borks the illiad openurl.
            TODO: - consider massaging long-urls earlier...
                  - or consider passing in the short-link, then doing a lookup to get the original querystring.
            Called by views.login_handler() """
        last_char = querystring[-1:]
        if last_char == '%':  # handles failing ending like 'param=abc+d%'
            querystring = querystring[0:-1]
        flag = 'go'
        while flag == 'go':
            last_chars = querystring[-2:]
            if last_chars[0] == '%' and last_chars[1].isdigit():  # handles failing ending like 'param=abc+def%2'
                querystring= querystring[0:-2]
            else:
                flag = 'stop'
        log.debug( 'returning querystring, ```{}```'.format(querystring) )
        return querystring

    # def check_querystring( self, querystring ):
    #     """ Handles situation where querystring is truncated in the middle of character-encoding,
    #           leaving a badly-formed openurl which borks the illiad openurl.
    #         TODO: - consider massaging long-urls earlier...
    #               - or consider passing in the short-link, then doing a lookup to get the original querystring.
    #         Called by views.login_handler() """
    #     flag = 'go'
    #     while flag == 'go':
    #         last_chars = querystring[-2:]
    #         if last_chars[0] == '%' and last_chars[1].isdigit():
    #             querystring= querystring[0:-2]
    #         else:
    #             flag = 'stop'
    #     log.debug( 'returning querystring, ```{}```'.format(querystring) )
    #     return querystring

    def update_user( self, localdev, meta_dct, host ):
        """ For now just returns shib_dct, with courses removed to make it shorter (it'll be jsonized into the session);
            eventually with create or update a user object and return that.
            Called by views.login_handler() """
        if localdev is False:
            ( shib_dct, filtered_memberships ) = ( shib_checker.grab_shib_info(meta_dct, host), [] )
            memberships = shib_dct['member_of']
            for membership in memberships:
                if membership[0:7] != 'COURSE:':
                    filtered_memberships.append( membership )
            shib_dct['member_of'] = filtered_memberships
        else:  # localdev
            shib_dct = settings_app.DEVELOPMENT_SHIB_DCT
        log.debug( 'shib_dct, `%s`' % pprint.pformat(shib_dct) )
        return shib_dct

    # end class LoginViewHelper()
