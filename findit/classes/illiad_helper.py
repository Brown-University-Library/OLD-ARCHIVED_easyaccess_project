# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint, random, urllib
import urlparse  # remove?
import bibjsontools  # requirements.txt module
from findit import app_settings


log = logging.getLogger('access')


class IlliadUrlBuilder( object ):
    """ Constructs url sent to illiad.
        Called by FinditResolver() code. """

    def __init__( self ):
        self.validator = IlliadValidator()

    def make_illiad_url( self, initial_querystring ):
        """ Manages steps of constructing illiad url.
            Called by FinditResolver.update_session() """
        bib_dct = bibjsontools.from_openurl( initial_querystring )
        ill_bib_dct = self.validator.add_required_kvs( bib_dct )
        extra_dct = self.check_identifiers( ill_bib_dct )
        extra_dct = self.check_validity( ill_bib_dct, extra_dct )
        openurl = bibjsontools.to_openurl( ill_bib_dct )
        for k,v in extra_dct.iteritems():
            openurl += '&%s=%s' % ( urllib.quote_plus(k), urllib.quote_plus(v) )
        illiad_url = app_settings.ILLIAD_URL_ROOT % openurl  # ILLIAD_URL_ROOT is like `http...OpenURL?%s
        log.debug( 'illiad_url, ```%s```' % illiad_url )
        return illiad_url

    def check_identifiers( self, ill_bib_dct ):
        """ Gets oclc or pubmed IDs.
            Called by make_illiad_url() """
        extra_dct = {}
        identifiers = ill_bib_dct.get( 'identifier', [] )
        for idt in identifiers:
            if idt['type'] == 'pmid':
                extra_dct['Notes'] = 'PMID: %s.\r via easyAccess' % idt['id']
            elif idt['type'] == 'oclc':
                extra_dct['ESPNumber'] = idt['id']
        return extra_dct

    def check_validity( self, ill_bib_dct, extra_dct ):
        """ Updates notes if necessary based on IlliadValidator.add_required_kvs() work.
            Called by make_illiad_url() """
        if ill_bib_dct.get('_valid') is not True:
            if extra_dct.get('Notes') is None:
                extra_dct['Notes'] = ''
            extra_dct['Notes'] += '\rNot enough data provided by original request.'
        return extra_dct

    # end class IlliadHelper


class IlliadValidator( object ):
    """ Adds required keys and values for illiad.
        Called by IlliadHelper.make_illiad_url() """

    def add_required_kvs( self, bib_dct ):
        """ Adds required keys and values for illiad.
            Called by IlliadHelper.make_illiad_url() """
        valid_check = True
        if bib_dct['type'] == 'article':
            ( bib_dct, valid_check ) = self._handle_article( bib_dct, valid_check )
        elif bib_dct['type'] == 'book':
            ( bib_dct, valid_check ) = self._handle_book( bib_dct, valid_check )
        elif (bib_dct['type'] == 'bookitem') or (bib_dct['type'] == 'inbook'):  # TL: These should all be inbooks but checking for now.
            ( bib_dct, valid_check ) = self._handle_bookish( bib_dct, valid_check )
        bib_dct['_valid'] = valid_check
        return bib_dct

    def _handle_article( self, bib_dct, valid_check ):
        """ Updates bib_dct with article values.
            Called by add_required_kvs() """
        if bib_dct.get('journal') is None:
            bib_dct['journal'] = {'name': 'Not provided'}; valid_check = False
        if bib_dct.get('year') is None:
            bib_dct['year'] = '?'; valid_check = False
        if bib_dct.get('title') is None:
            bib_dct['title'] = 'Title not specified'; valid_check = False
        if bib_dct.get('pages') is None:
            bib_dct['pages'] = '? - ?'; valid_check = False
        return ( bib_dct, valid_check )

    def _handle_book( self, bib_dct, valid_check ):
        """ Updates bib_dct with book values.
            Called by add_required_kvs() """
        if bib_dct.get('title') is None:
            bib_dct['title'] = 'Not available'
            valid = False
        return ( bib_dct, valid_check )

    def _handle_bookish( self, bib_dct, valid_check ):
        """ Updates bib_dct with bookitem or inbook values.
            Called by add_required_kvs() """
        if bib_dct.get('title') is None:
            bib_dct['title'] = 'Title not specified'; valid_check = False
        if bib_dct.get('journal') is None:
            bib_dct['journal'] = {'name': 'Source not provided'}; valid_check = False
        pages = bib_dct.get('pages')
        if (pages == []) or (pages is None):
            bib_dct['pages'] = '? - ?'; valid_check = False
        return ( bib_dct, valid_check )

    # end class IlliadValidator


    # def make_illiad_url( self, bibjson ):
    #     """
    #     Create an Illiad request URL from bibsjon.  Requires adding a couple of
    #     Illiad specific fields.
    #     Called by...
    #     """
    #     # from bibjsontools import to_openurl
    #     base = app_settings.ILLIAD_URL
    #     #Send to validate_bib to add default values missing fields.
    #     bib = self.illiad_validate(bibjson)
    #     #Holder for values to add to the raw openurl
    #     extra = {}
    #     #Get OCLC or pubmed IDS
    #     identifiers = bibjson.get('identifier', [])
    #     for idt in identifiers:
    #         if idt['type'] == 'pmid':
    #             extra['Notes'] = "PMID: %s.\r via easyAccess" % idt['id']
    #         elif idt['type'] == 'oclc':
    #             extra['ESPNumber'] = idt['id']
    #     if bib.get('_valid') is not True:
    #         if extra.get('Notes') is None:
    #             extra['Notes'] = ''
    #         extra['Notes'] += "\rNot enough data provided by original request."
    #     ourl = bibjsontools.to_openurl(bib)
    #     for k,v in extra.iteritems():
    #         ourl += "&%s=%s" % (urllib.quote_plus(k), urllib.quote_plus(v))
    #     illiad = base % ourl
    #     return illiad


    # def illiad_validate( self, bib ):
    #     """
    #     Validates a bibjson objects for Illiad.
    #     It simply adds default values for required fields that are
    #     missing.
    #     Called by make_illiad_url()
    #     """
    #     valid = True
    #     if bib['type'] == 'article':
    #         if bib.get('journal') is None:
    #             d = {'name': 'Not provided'}
    #             bib['journal'] = d
    #             valid = False
    #         if bib.get('year') is None:
    #             bib['year'] = '?'
    #             valid = False
    #         if bib.get('title') is None:
    #             bib['title'] = "Title not specified"
    #             valid = False
    #         if bib.get('pages') is None:
    #             bib['pages'] = '? - ?'
    #             valid = False
    #     elif bib['type'] == 'book':
    #         if bib.get('title') is None:
    #             bib['title'] = 'Not available'
    #             valid = False
    #     #These should all be inbooks but checking for now.
    #     elif (bib['type'] == 'bookitem') or (bib['type'] == 'inbook'):
    #         if bib.get('title') is None:
    #             bib['title'] = "Title not specified"
    #             valid = False
    #         if bib.get('journal') is None:
    #             d = {'name': 'Source not provided'}
    #             bib['journal'] = d
    #             valid = False
    #         pages = bib.get('pages')
    #         if (pages == []) or (pages is None):
    #             bib['pages'] = '? - ?'
    #             valid = False
    #     bib['_valid'] = valid
    #     return bib



