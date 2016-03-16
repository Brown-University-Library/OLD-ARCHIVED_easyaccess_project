
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
from django.test import TestCase
from delivery.classes.process_helper import ProcessViewHelper


log = logging.getLogger('access')
log.debug( 'testing123' )



class ProcessHelperTest(TestCase):
    """ Checks availability views """

    def setUp(self):
        self.helper = ProcessViewHelper()

    def test_save_to_easyborrow(self):
        """ Good shib & citation should allow save. """
        bib_dct = {}
        shib_dct = {}
        querystring = ''
        self.assertEqual( 1, self.helper.save_to_easyborrow(shib_dct, bib_dct, querystring) )

    # end ProcessHelperTest()

