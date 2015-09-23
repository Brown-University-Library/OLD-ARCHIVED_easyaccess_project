"""
This is an attempt to parse out incoming OpenUrls into
citation objects that can be displayed to user and trigger
client side requests for services - like full text, abstract, citing articles,
etc.
"""

import sys
import urlparse
import urllib
from pprint import pprint


"""
format
title
source
primary author
authors - l
date - year
pages
publisher
doi
pmid
isbn - l
issn - l
oclc - l

optional
pdf
html
"""


data = open(sys.argv[1])


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
        skips = ['rft_val_fmt', 'id', 'rfr_id', 'url_ver',
                 'url_ctx_fmt', 'rft_id', 'openurl', 'req_dat',
                 'sid', '__char_set']
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



c = {}
def make_cite(qdict):
    #get dois or pmid
    id = qd.get('id', None)
    if not id:
        return
    for e in id:
        idt, val = e.split(':')
        print idt, val
        c[idt] = val
        pprint(c)

