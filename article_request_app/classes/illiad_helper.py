# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random


log = logging.getLogger('access')


class IlliadHelper( object ):
    """ Contains helpers for views.login() """

    def make_illiad_blocked_message( self, firstname, lastname, citation ):
        """ Preps illiad blocked message.
            Called by build_message() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyArticle service. It appears there is a problem with your Interlibrary Loan, ILLiad account.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    ''' % (
        firstname,
        lastname,
        citation )
        log.debug( 'illiad blocked message built, ```%s```' % message )
        return message
        ### end make_illiad_blocked_message() ###

    def make_illiad_unregistered_message( self, firstname, lastname, citation ):
        """ Preps illiad blocked message.
            Called by build_message() """
        message = '''
Greetings %s %s,

Your request for the item, '%s', could not be fulfilled by our easyAccess service. There was a problem trying to register you with 'ILLiad', our interlibrary-loan service.

Contact the Interlibrary Loan office at interlibrary_loan@brown.edu or at 401/863-2169. The staff will work with you to resolve the problem.

[end]
    ''' % (
        firstname,
        lastname,
        citation )
        log.debug( 'illiad unregistered message built, ```%s```' % message )
        return message
        ### end make_illiad_unregistered_message() ###
