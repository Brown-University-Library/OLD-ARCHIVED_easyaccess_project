"""
Lookup PMIDS and parse the returned metadata into the BibJSON format.  

See: http://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch

"""

from lxml import etree
import urllib
from pprint import pprint

from bibjsontools import to_openurl

class BibJSON(object):
    def __init__(self, pmid):
        self.pmid = pmid
        handle = urllib.urlopen('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=%s' % pmid)
        self.doc = etree.parse(handle)
        self.dsum = self.doc.xpath('/eSummaryResult/DocSum')[0]

    def _x(self, path, text=True):
        if text:
            return self.dsum.xpath('%s/text()' % path)[0]
        else:
            return self.dsum.xpath(path)

    def _name(self, name):
        try:
            return self._x('Item[@Name="%s"][1]' % name)
        except IndexError:
            return ''

    def identifiers(self):
        out = [
            {'type': 'pmid',
            'value': 'pmid:%s' % self.pmid}
        ]
        d = {'type': 'doi',
          'value': "doi:%s" % self._name('DOI')}
        out.append(d)
        d = {}
        for k in ['ISSN', 'ESSN']:
            v = self._name(k)
            if v != '':
                if k == 'ESSN':
                    k = 'eissn'
                out.append({'type': k.lower(), 'value': v})

        #Look at article ids section
        aids = self.doc.xpath('/eSummaryResult/DocSum/Item[@Name="ArticleIds"]')[0]
        for aid in aids:
            if aid.get('Name') == 'pmc':
                out.append({'type': 'pmcid', 'value': aid.text})
        #Try pubmed central id
        #pmc = self.xpath
        return out

    def authors(self):
        #author => [{'lastname': 'Frogner', 'name': 'BK Frogner', 'firstname': 'BK'}]
        out = []
        author_list = self.doc.xpath('/eSummaryResult/DocSum/Item[@Name="AuthorList"]')[0]
        for auth in author_list:
            out.append({'name': auth.text})
        return out

    def type(self):
        try:
            pub = self.doc.xpath('/eSummaryResult/DocSum/Item/Item[@Name="PubType"]')[0].text
        except IndexError:
            return 'article'
        if pub == 'Journal Article':
            return 'article'
        return pub

    def parse(self):
        def _name(name):
            try:
                return self._x('Item[@Name="%s"][1]' % name)
            except IndexError:
                return ''
        b = {}
        b['type'] = self.type()
        b['title'] = _name('Title')
        b['year'] = _name('PubDate')[:4]
        b['volume'] = _name('Volume')
        b['issue'] = _name('Issue')
        b['pages'] = _name('Pages')
        if b['pages'] != '':
            chunks = b['pages'].split('-')
            b['start_page'] = chunks[0]
            try:
                b['end_page'] = chunks[1]
            except IndexError:
                b['end_page'] = 'EOA'
        b['journal'] = {'name': _name('FullJournalName'),
                        'shortcode': _name('Source')}
        b['_pubstatus'] = _name('PubStatus')

        b['identifiers'] = self.identifiers()
        b['link'] = []
        for bid in b['identifiers']:
            if bid['type'] == 'pmcid':
                b['link'].append({'anchor': 'Full text from PubMed Central',
                                  'url': 'http://www.ncbi.nlm.nih.gov/pmc/articles/%s' % bid['value']})
        if b['link'] == []:
            del b['link']

        b['author'] = self.authors()

        return b

def to_bibjson(pmid):
    d = BibJSON(pmid).parse()
    d['_openurl'] = to_openurl(d)
    return d