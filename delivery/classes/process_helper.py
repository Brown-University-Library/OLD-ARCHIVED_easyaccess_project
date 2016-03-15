# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging


log = logging.getLogger('access')


class ProcessViewHelper(object):
    """ Contains helpers for views.login() """

    def __init__(self):
        pass

    def foo( self, session, meta_dict ):
        """ Ensures request came from findit app.
            Called by views.login() """
        pass

    # end class ProcessViewHelper()
