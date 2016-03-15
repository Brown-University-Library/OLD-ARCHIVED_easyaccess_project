# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging


log = logging.getLogger('access')


class LoginViewHelper(object):
    """ Contains helpers for views.login() """

    def __init__(self):
        pass

    def check_referrer( self, session, meta_dict ):
        """ Ensures request came from findit app.
            Called by views.login() """
        referrer_ok = False
        findit_illiad_check_flag = session.get( 'findit_illiad_check_flag', '' )
        findit_illiad_check_openurl = session.get( 'findit_illiad_check_enhanced_querystring', '' )
        if findit_illiad_check_flag == 'good' and findit_illiad_check_openurl == meta_dict.get('QUERY_STRING', ''):
            findit_check = True
        elif findit_check is not True:
            log.warning( 'Bad attempt from source-url, ```%s```; ip, `%s`' % (
                meta_dict.get('HTTP_REFERER', ''), meta_dict.get('REMOTE_ADDR', '') ) )
        log.debug( 'findit_check, `%s`' % findit_check )
        return findit_check

    # end class LoginViewHelper()
