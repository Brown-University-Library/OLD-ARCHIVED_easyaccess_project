
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
from django.test import TestCase
from delivery.classes.process_helper import ProcessViewHelper


log = logging.getLogger('access')
log.debug( 'testing123' )



class ProcessHelperTest(TestCase):
    """ Checks ProcessViewHelper()
        Not going to test save_to_easyborrow() with good data to avoid executing real request. """

    def setUp(self):
        self.helper = ProcessViewHelper()

    def test_save_to_easyborrow(self):
        """ Bad data. """
        bib_dct = {}
        shib_dct = {}
        querystring = ''
        self.assertEqual( None, self.helper.save_to_easyborrow(shib_dct, bib_dct, querystring) )  # a good save would return the ezb-db-id

    # end ProcessHelperTest()

