"""
Export citation in various formats.  Using service built into 360Link.
RIS format is the only type implemented at the moment.  
"""

"""
citation: {
eissn: "1531-6564",
creatorLast: "Schlenker",
creator: "Schlenker, J D",
title: "Three complications of untreated partial laceration of flexor tendon--entrapment, rupture, and triggering",
volume: "6",
source: "The Journal of hand surgery (American ed.)",
creatorFirst: "J",
date: "1981-07",
creatorMiddle: "D",
spage: "392",
issue: "4",
pmid: "7252116",
issn: {
print: "0363-5023"
}
Provider: 360 Link
Database:
Tagformat:
Content: text/plain; charset="UTF-8"


TY  - BOOK
AU  - Dyson, Stephen L
SN  - 978-0-300-11097-5
JO  - In pursuit of ancient pasts : a history of classical archaeology in the nineteenth and twentieth centuries
PY  - 2006
PB  - Yale University Press
CP  - New Haven
ER  - 

#Book part
Provider: 360 Link
Database:
Tagformat:
Content: text/plain; charset="UTF-8"


TY  - JOUR
TI  - SYTO probes: markers of apoptotic cell demise
AU  - Wlodkowic, Donald
SN  - 1934-9300
SN  - 978-0-471-14295-9
JO  - Current Protocols in Cytometry
PY  - 2007/10
SP  - Unit7.33
VL  - Chapter 7
CP  - Hoboken, NJ, USA
DO  - 10.1002/0471142956.cy0733s42
N1  - PMID: 18770855
ER  - 

Provider: 360 Link
Database:
Tagformat:
Content: text/plain; charset="UTF-8"


TY  - JOUR
TI  - Phylogeny and divergence time of island tiger beetles of the genus Cylindera (Coleoptera: Cicindelidae) in East Asia PHYLOGENY OF TIGER BEETLES IN EAST ASIA
AU  - SOTA, TEIJI
SN  - 0024-4066
JO  - Biological journal of the Linnean Society
PY  - 2011/04
SP  - 715
EP  - 727
VL  - 102
IS  - 4
PB  - Published for the Linnean Society of London by Blackwell [etc
DO  - 10.1111/j.1095-8312.2011.01617.x
ER  - 

citation: {
issn: {
print: "0024-4066",
electronic: "1095-8312"
},
creator: "SOTA, TEIJI",
creatorLast: "SOTA",
source: "Biological journal of the Linnean Society",
creatorFirst: "TEIJI",
date: "2011-04",
title: "Phylogeny and divergence time of island tiger beetles of the genus Cylindera (Coleoptera: Cicindelidae) in East Asia PHYLOGENY OF TIGER BEETLES IN EAST ASIA",
spage: "715",
issue: "4"
},

"""

def _mapper(key, format):
        """
        Maps 360Link citation to RIS.
        http://en.wikipedia.org/wiki/RIS_(file_format)
        
        Adding pubmed IDS to the AN field per:
        http://forums.zotero.org/discussion/5404/pubmed-id/
        """
        common = {
              'creator': 'AU',
              'date': 'PY',
              'volume': 'VL',
              'issue': 'IS',
              'spage': 'SP',
              'publisher': 'PB',
              'publicationPlace': 'CY',
              'pmid': 'AN',
        }
        _j = {
              'title': 'TI',
              'source': 'JO',
              'doi': 'DO',
        }
        _b = {
            'title': 'TI',
            'source': 'JO',
            'publicationPlace': 'place',
        }
        _j.update(common)
        _b.update(common)
        #Treat everything as a book unless it is a journal.
        if format == 'journal':
            try:
                return _j[key]
            except KeyError:
                pass
        else:
            try:
                return _b[key]
            except KeyError:
                pass
        #default is to return original key
        return key
    

def ris(citation, format):
    import re
    #map
    ris = dict(map(lambda (key, value): (_mapper(str(key), format), value), citation.items()))
    if format == 'journal':
        ris['TY'] = 'JOUR'
    else:
        ris['TY'] = 'BOOK'
    #convert to string
    out = """Provider: 360 Link
    Database:
    Tagformat:
    Content: text/plain; charset="UTF-8"\n\n
    """
    out = ""
    
    for k,v in ris.items():
        #Skip non-RIS keys.
        if not re.match('[A-Z]{2}', k):
            continue
        #Munge year
        if k == 'PY':
            v = v.split('-')[0] + '///'
        out += "%s  - %s\n" % (k, v)
    
    return out