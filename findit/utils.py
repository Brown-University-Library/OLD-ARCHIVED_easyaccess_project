# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, urlparse
from datetime import datetime


from . import forms, summon
from .app_settings import DB_SORT_BY, DB_PUSH_TOP, DB_PUSH_BOTTOM
from .app_settings import PRINT_PROVIDER
from .models import PrintTitle
from django.conf import settings
from django.utils.log import dictConfig
from py360link2 import Resolved


CURRENT_YEAR = datetime.now().year


dictConfig( settings.LOGGING )
log = logging.getLogger('access')



class FinditResolver( object ):
    """ Handles findit resolver calls. """

    def __init__(self):
        self.enhanced_link = False

    def get_referrer( self, querydict ):
        """ Gets the referring site to append to links headed elsewhere.
            Helpful for tracking down ILL request sources.
            Called by views.base_resolver() """
        ( sid, ea ) = ( None, 'easyAccess' )
        sid = querydict.get( 'sid', None )
        if not sid:  # then try rfr_id
            sid = querydict.get( 'rfr_id', None )
        if sid:
            referrer = '%s-%s' % ( sid, ea )
        else:
            referrer = ea
        log.debug( 'referrer, `%s`' % referrer )
        return referrer

    def check_summon( self, referrer ):
        """ Determines whether a summon check is needed.
            Called by views.base_resolver() """
        check_summon = True
        for provider in settings.FINDIT_SKIP_SUMMON_DIRECT_LINK:
            if referrer.find( provider ) > 0:
                check_summon = False
                break
        log.debug( 'check_summon, `%s`' % check_summon )
        return check_summon

    def enhance_link( self, direct_indicator, query_string ):
        """ Enhances link via summon lookup if necessary. """
        enhanced = False
        if direct_indicator is not 'false':  # ensure the GET request doesn't override this (bjd: don't fully understand this; i assume this val is set somewhere)
            enhanced_link = summon.get_enhanced_link( query_string )  # TODO - use the metadata from Summon to render the request page rather than hitting the 360Link API for something that is known not to be held.
            log.debug( "enhanced_link, `%s`" % enhanced_link )
            if enhanced_link:
                self.enhanced_link = enhanced_link
                enhanced = True
        return enhanced

    # end class FinditResolver   request.META.get('QUERY_STRING', None)


class BulSerSol(Resolved):
    """
    Sub-class of the main Resolved class to handle Browns specific needs.
    """
    def pull_print(self, issns):
        """
        Get the print title information and return Django query object.
        """
        #Normalize start and end - dates are 2007-01-01.
        #import ipdb; ipdb.set_trace()
#        start = int(start.split('-')[0])
#        try:
#            end = int(end.split('-')[0])
#        except IndexError:
#            #set this for open ended dates.
#            end = 4000
        date = self.citation.get('date', None)
        if date:
            date = date[:4]
            print_set = PrintTitle.objects.filter(issn__in=issns,
                                                     start__lte=date,
                                                     end__gte=date)
            return print_set
        else:
            return []

    def get_non_direct(self, group):
        """
        Get non-direct links from a link group.  These are journals only.
        """
        #Dict to hold the link
        d = {}
        d['link'] = None
        d['type'] = None
        #Provider
        d['name'] = group['holdingData']['databaseName']
        #Try issue
        issue = group['url'].get('issue', None)
        journal = group['url'].get('journal', None)
        if issue:
            d['link'] = issue
            d['type'] = 'issue'
        elif journal:
            d['link'] = journal
            d['type'] = 'journal'
        else:
            return
        return d

    def do_db_sort(self, link_groups):
        """
        Sort the links returned by library defined criteria.
        http://stackoverflow.com/questions/10274868/sort-a-list-of-python-dictionaries-depending-on-a-ordered-criteria

        A low or negative value will bring the link to the top of the list.
        A low or negative value will push the link to the bottom of the list.
        """
        criteria = DB_SORT_BY
        def _mapped(provider):
            if provider in DB_PUSH_TOP:
                return -100
            elif provider in DB_PUSH_BOTTOM:
                return 100
            else:
                try:
                    return criteria.index(provider)
                except ValueError:
                    #Return 99 .  The lowest value a db in the criteria list
                    #could have is 0 up to the length of the list.  If the
                    #db is not found.  Return something high so that all
                    #dbs not specified are treated the same.
                    return 99
        link_groups.sort(key=lambda x: _mapped(x['holdingData']['providerName']))
        return link_groups

    def access_points(self):
        """
        Pull out all of the 'source' urls and put them into a dict
        with name, link keys.

        Return dict with direct link and full link groups.
        """
        raw_link_groups = self.link_groups
        #Sort the link groups
        link_groups = self.do_db_sort(raw_link_groups)
        issns = [self.citation.get('eissn', None)]
        issns += self.citation.get('issn', {}).values()
        resolved_issn = self.citation.get('issn', None)
        if resolved_issn:
            pissn = resolved_issn.get('print', None)
            if pissn :
                issns.append(pissn)
        online = []
        direct = None
        vague_links = False
        pholdings = []
        #Holder so we don't duplicate the print holdings.
        seen_print = []
        for group in link_groups:
            this_holding = {}
            name = group['holdingData']['databaseName']
            #Check for print
            if name == PRINT_PROVIDER:
                #database of print titles to get location and call number.
                print_held = {}
                #hd = group['holdingData']
                #print_held['start'] = hd['startDate']
                #print_held['end'] = hd.get('endDate', str(CURRENT_YEAR))
                #We want anything with same issn and start greater than or equal to this start and end less than this cite.
                print_titles = self.pull_print(issns)
                for item in print_titles:
                    print_held['location'] = item.location
                    print_held['call_number'] = item.call_number
                    #We are checking this pair of print items - location + call number
                    #against a list of seen locations to prevent duplicate holdings from
                    #appearing.  360Link seems to be returning multiple sets in some cases.
                    pair = (print_held['location'],
                            print_held['call_number'])
                    if pair not in seen_print:
                        seen_print.append(pair)
                        pholdings.append(print_held)
            else:
                #Handle book and article links.
                if self.format == 'book':
                    #For 'books' that are actually chapters we want the article
                    #level link returned by SerSol.
                    dl = group['url'].get('article', None)
                    #If that is empty, get the book level link.
                    if not dl:
                        dl = group['url'].get('book', None)

                else:
                    #Handle journals.
                    #Try to get a direct link first
                    dl = group['url'].get('article', None)
                    if dl:
                        this_holding['link'] = dl
                        this_holding['name'] = name
                        this_holding['type'] = 'direct'
                        if direct is None:
                            direct = {'provider': name, 'link' : dl}
                    else:
                        #Non-direct to full text links.
                        not_direct = self.get_non_direct(group)
                        if not_direct:
                            vague_links = True
                            this_holding = not_direct

                    #Only add links that aren't duplicates
                    if this_holding['link'] not in [n['link'] for n in online]:
                        if this_holding['name'] not in [n['name'] for n in online]:
                            online.append(this_holding)

        if ((len(pholdings) == 0) and\
            (len(online) == 0)):
            resolved = False
        else:
            resolved = True

        #Change vague_links to false if we did find a direct link.  This prevents
        #the warning/caveat box from appearing.
        #Template will prevent non direct links from displaying to users.
        if direct:
            vague_links = False
            #Remove non-direc links from the online
            for n, link in enumerate(online):
                if link['type'] != 'direct':
                    del online[n]

        return {'direct_link': direct,
                'online': online,
                'print': pholdings,
                'resolved': resolved,
                'has_vague_links': vague_links}

    def is_requestable(self):
        """
        Look at the available metadata and make sure that the items is requestable
        via Illiad with the given metadata.
        """
        title = self.citation.get('title', None)
        source = self.citation.get('source', None)
        date = self.citation.get('date', None)
        if self.format == 'book':
            #Requiring, title, date, encouraging ISBN and OCLC number
            if ((title or source is not None) and date is not None):
                return True
        elif self.format == 'journal':
            #Requiring title, source, date/year, pages
            pages = self.citation.get('spage', None)
            if title is not None:
                if source is not None:
                    if date is not None:
                        if pages is not None:
                            return True
            return False
        #How should we validate other metdata - require OCLC number?
        else:
            return True

    def get_citation_form(self):
        return self.prep_resolver_form()

    def _mapper(self, key, format):
        """
        Maps 360Link returned values to the citation linker form.
        """
        common = {
              'creator': 'au',
              'creatorLast': 'aulast',
              'creatorFirst': 'aufirst',
        }
        _j = {
              'title': 'atitle',
              'source': 'jtitle',
              'doi': 'id',
        }
        _b = {
            'title': 'btitle',
            'source': 'btitle',
            'publisher': 'pub',
            'publicationPlace': 'place',
        }
        _j.update(common)
        _b.update(common)
        if format == 'journal':
            try:
                return _j[key]
            except KeyError:
                pass
        elif format == 'book':
            try:
                return _b[key]
            except KeyError:
                pass
        #now handle other forms - treat all as books for now.
        else:
            try:
                return _b[key]
            except KeyError:
                pass
        #default is to return original key
        return key

    def citation_form_dict(self):
        """
        Map the resolved citation to the form field names.
        Putting the original OCLC number, if present, in rfe_dat
        """
        #Sent to 360 link to get a citation object.
        query = self.query
        citation = self.citation
        format = self.format
        #Always just use the first issn or isbn
        issn = citation.get('issn', None)
        if issn:
            citation['issn'] = issn.values()[0]
        isbn = citation.get('isbn', None)
        if isbn:
            citation['isbn'] = isbn[0]
        #mapping lambda from http://stackoverflow.com/questions/2213334/in-python-i-have-a-dictionary-how-do-i-change-the-keys-of-this-dictionary
        cd = dict(map(lambda (key, value): (self._mapper(str(key), format), value), citation.items()))
        citation_form_dict = cd
        citation_form_dict['rfe_dat'] = self.oclc_number
        #massage pages.
        pages = citation_form_dict.get('pages', None)
        if not pages:
            spage = citation_form_dict.get('spage', None)
            epage = citation_form_dict.get('epage', None)
            if spage:
                if epage:
                    cpages = "%s-%s" % (spage, epage)
                else:
                    cpages = "%s-EOA" % (spage)
                citation_form_dict['pages'] = cpages
        return citation_form_dict


    def prep_resolver_form(self):
        citation_form_dict = self.citation_form_dict()
        d = {}
        format = self.format
        #Hook in forms.
        if format == 'journal':
            #citation_form_dict['title'] = citation['atitle']
            d['form_type'] = 'article'
        else:
            d['form_type'] = format

        d['article_form'] = forms.ArticleForm(citation_form_dict)
        d['book_form'] = forms.BookForm(citation_form_dict)
        d['dissertation_form'] = forms.DissertationForm(citation_form_dict)
        d['patent_form'] = forms.PatentForm(citation_form_dict)
        return d

    def easy_borrow_query(self):
        """
        Construct a query that can be passed on to easyBorrow.
        This is just going to be the SerSol citation plus the original OCLC
        number passed in, if any.
        """
        import urllib
        qdict = self.citation
        #Massage authors
        qdict['author'] = qdict.get('creator', None)
        #del qdict['creator']
        qdict['aulast'] = qdict.get('creatorLast', None)
        #put source in title
        if qdict.get('title', None) is None:
            qdict['title'] = qdict.get('source', None)
        #del qdict['creatorLast']
        #do genre
        if self.format == 'book':
            qdict['genre'] = 'book'
        else:
            qdict['genre'] = 'article'
        #Add the OCLC number
        qdict['rfe_dat'] = self.oclc_number
        return urllib.urlencode(qdict, doseq=True)


#===============================================================================
# Illiad URLs
#===============================================================================
def pull_genre(odict):
    possible_keys = ['rft.genre', 'genre']
    for p in possible_keys:
        genre = odict.get(p, ['null'])[0]
        if genre == 'journal':
            genre = 'article'
        #take the first one we find.
        if genre != 'null':
            break
    if genre == 'article':
        return genre
    elif genre == 'null':
        #Try too determine format by looking at some characteristics.
        #doi = odict.get('rft_id', [''])
        return None
    #last guess
    else:
        return 'book'

def pull_oclc(odict):
    import re
    oclc_reg = re.compile('\d+')
    oclc = None
    if odict.get('rfr_id', ['null'])[0].rfind('firstsearch') > -1:
        oclc = odict.get('rfe_dat', ['null'])[0]
        match = oclc_reg.search(oclc)
        if match:
            oclc = match.group()
    return oclc

def pull_referrer(odict):
    ea='bul_easy_article'
    sid = odict.get('sid', None)
    #Try rfr_id if not found in sid.
    if not sid:
        sid = odict.get('rfr_id', None)
    if sid:
        return sid
        #return ['%s-%s' % (s, ea) for s in sid]
    return []


def illiad_date(datestr):
    """
    Dates should be four digit years - 1990 - without issue or
    volume information, 'e.g. 1990-2'.  For RAPID per Bart.
    """
    #Deactivating date massaging per Bart - 3/14/13
    #Reactivating date massaging per Bart - 8/1/13
    #Bart wants raw dates again - 4/24/14
    return datestr
    #if datestr:
    #   return datestr.split('-')[0]
    #else:
    #   return


def make_illiad_url(openurl):
    import urlparse
    import urllib
    o = urllib.unquote(openurl)
    odict = urlparse.parse_qs(o)
    #pprint(odict)
    out = odict
    #out['sid'] = sid
    #Switch the genre to book if it's not an article.
    genre = pull_genre(odict)
    #Delete original genres.
    try:
        del out['rft.genre']
        del out['genre']
    except KeyError:
        pass
    if genre:
        out['rft.genre'] = genre
    #massage date to be four character year - 1990 not 1990-2
    out['rft.date'] = illiad_date(out.get('rft.date', [''])[0])
    #Get pubmed if we can find it and put into the Notes field.
    pmid = odict.get('pmid', None)
    if not pmid:
        for ident in odict.get('rft_id', []):
            if ident.startswith('info:/pmid/'):
                pmid = indent
                out['Notes'] = "PMID: %s" % pmid[0]
                break
    else:
        out['Notes'] = "PMID: %s" % pmid[0]
    #get oclc number
    oclc = pull_oclc(odict)
    if oclc:
        out['ESPNumber'] = oclc
    #get referring site
    out['sid'] = pull_referrer(odict)
    #Change an empty end page to EOA for end of article per Bart.
    endpage = odict.get('rft.epage', None)
    if (not endpage) or (endpage == ''):
        out['rft.epage'] =  'EOA'
    ourl = urllib.urlencode(out, doseq=True)
    return ourl

#===============================================================================
# Raw open url parsing.
#===============================================================================
class Ourl(object):
    def __init__(self, query):
        self.query = query
        self.qdict = urlparse.parse_qs(query)
        self.cite = {}

    def make_cite(self):
        self.pull_id()
        self.prest()
        self.pull_oclc()

    def pull_id(self):
        #get id param
        id = self.qdict.get('id', [])
        #see if pmid was passed in.
        id += ['pmid:%s' % p for p in self.qdict.get('pmid', []) if p]
        #or doi
        id += ['doi:%s' % d for d in self.qdict.get('doi', []) if d]
        #look at rft_id
        _t =  self.qdict.get('rft_id', None)
        if _t:
            for e in _t:
                if e.startswith('info:doi/'):
                    id.append('doi:%s' % e.lstrip('info:doi/'))
                elif e.startswith('info:pmid/'):
                    id.append('pmid:%s' % e.lstrip('info:pmid/'))
        if not id:
            return
        for e in id:
            chunked = e.split(':')
            idt = chunked[0]
            val = ''.join(chunked[1:])
            self.cite[idt] = val

    def format(self):
        f = self.qdict.get('rft_val_fmt', [':'])[0].split(':')[-1]
        if f == '':
            return 'unknown'
        else:
            return f

    def prest(self):
        #Maybe turn these into items to check rather than items to skip
        skips = ['rft_val_fmt', 'id', 'url_ver',
                 'url_ctx_fmt', 'rft_id', 'openurl', 'req_dat',
                 '__char_set']
        for k, v in self.qdict.items():
            v = [e.strip() for e in v]
            if (k == 'rft.genre') or (k == 'genre'):
                k = 'format'
                #del self.qdict['genre']
            if k in skips:
                continue
            else:
                k = k.replace('rft.', '')
                self.cite[k] = v[0]

    def pull_oclc(self):
        import re
        oclc_reg = re.compile('\d+')
        oclc = None
        if self.qdict.get('rfr_id', ['null'])[0].rfind('firstsearch') > -1:
            oclc = self.qdict.get('rfe_dat', ['null'])[0]
            match = oclc_reg.search(oclc)
            if match:
                oclc = match.group()
        self.cite['oclc'] = oclc

#===============================================================================
# Utility for making cache keys for the extra utilities.
#===============================================================================
def get_cache_key(query):
    """
    Makes a hash of an incoming query for use as a cache key.
    """
    import hashlib
    key = hashlib.md5(repr(query)).hexdigest()
    return key
