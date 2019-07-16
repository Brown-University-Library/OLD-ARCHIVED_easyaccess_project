# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, urllib
# import urlparse  # remove?
import bibjsontools  # requirements.txt module
from findit import app_settings


log = logging.getLogger('access')


class IlliadUrlBuilder( object ):
    """ Constructs url sent to illiad.
        Called by FinditResolver() code. """

    def __init__( self ):
        self.validator = IlliadValidator()

    # def make_illiad_url( self, initial_querystring, permalink ):
    #     """ Manages steps of constructing illiad url for possible use in article-requesting.
    #         Called by FinditResolver.update_session() """
    #     bib_dct = bibjsontools.from_openurl( initial_querystring )
    #     ill_bib_dct = self.validator.add_required_kvs( bib_dct )
    #     log.debug( 'validator call complete' )
    #     extra_dct = self.check_identifiers( ill_bib_dct )
    #     log.debug( 'check_identifiers call complete' )
    #     extra_dct = self.check_validity( ill_bib_dct, extra_dct )
    #     log.debug( 'check_validity call complete' )
    #     extra_dct['Notes'] = self.update_note( extra_dct.get('Notes', ''), '`shortlink: <{}>`'.format(permalink) )
    #     openurl = bibjsontools.to_openurl( ill_bib_dct )
    #     for k, v in extra_dct.iteritems():
    #         openurl += '&%s=%s' % ( urllib.quote_plus(k), urllib.quote_plus(v) )
    #     illiad_url = app_settings.ILLIAD_URL_ROOT % openurl  # ILLIAD_URL_ROOT is like `http...OpenURL?%s
    #     log.debug( 'illiad_url, ```%s```' % illiad_url )
    #     return illiad_url

    def make_illiad_url( self, initial_querystring, scheme, host, permalink ):
        """ Manages steps of constructing illiad url for possible use in article-requesting.
            Called by FinditResolver.update_session() """
        bib_dct = bibjsontools.from_openurl( initial_querystring )
        ill_bib_dct = self.validator.add_required_kvs( bib_dct )
        log.debug( 'validator call complete' )
        extra_dct = self.check_identifiers( ill_bib_dct )
        log.debug( 'check_identifiers call complete' )
        extra_dct = self.check_validity( ill_bib_dct, extra_dct )
        log.debug( 'check_validity call complete' )
        # extra_dct['Notes'] = self.update_note( extra_dct.get('Notes', ''), '`shortlink: <{}>`'.format(permalink) )
        full_permalink = '%s://%s%s' % ( scheme, host, permalink )
        log.debug( 'full_permalink, ```%s```' % full_permalink )
        extra_dct['Notes'] = self.update_note( extra_dct.get('Notes', ''), '`shortlink: <%s>`' % full_permalink )
        openurl = bibjsontools.to_openurl( ill_bib_dct )
        # for k, v in extra_dct.iteritems():  # python2
        for k, v in extra_dct.items():
            # openurl += '&%s=%s' % ( urllib.quote_plus(k), urllib.quote_plus(v) )
            openurl += '&%s=%s' % ( urllib.parse.quote_plus(k), urllib.parse.quote_plus(v) )

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
                extra_dct['Notes'] = '`PMID: {}`'.format( idt['id'] )
                # extra_dct['Notes'] = self.update_note( 'foo', 'bar' )
            elif idt['type'] == 'oclc':
                extra_dct['ESPNumber'] = idt['id']
        return extra_dct

    def check_validity( self, ill_bib_dct, extra_dct ):
        """ Updates notes if necessary based on IlliadValidator.add_required_kvs() work.
            Called by make_illiad_url() """
        if ill_bib_dct.get('_valid') is not True:
            if extra_dct.get('Notes') is None:
                extra_dct['Notes'] = ''
            # extra_dct['Notes'] += '\rNot enough data provided by original request.'
            extra_dct['Notes'] = self.update_note( extra_dct['Notes'], '`not enough original-request data`' )
        return extra_dct

    def update_note( self, initial_note, additional_note ):
        """ Updates notes with correct spacing & punctuation.
            Called by check_identifiers(), check_validity(), make_illiad_url() """
        log.debug( 'starting update_note' )
        note = initial_note
        if note is None:
            note = additional_note
        elif len( note.strip() ) == 0:
            note = additional_note
        else:
            note += '; {}'.format( additional_note )
        log.debug( 'note now, ```{}```'.format(note) )
        return note

    # end class IlliadUrlBuilder


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
            valid_check = False
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
