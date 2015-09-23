#!/usr/bin/python 
#
# Convert Link360 XML To JSON
# follows http://xml.serialssolutions.com/ns/openurl/v1.0/ssopenurl.xsd
#
# Godmar Back <godmar@gmail.com>, May 2009
#

from lxml import etree

class Link360JSON(object):
    def __init__(self, doc):
        self.doc = doc

    def convert(self):

        ns = {
            "ss" : "http://xml.serialssolutions.com/ns/openurl/v1.0",
            "sd" : "http://xml.serialssolutions.com/ns/diagnostics/v1.0",
            "dc" : "http://purl.org/dc/elements/1.1/"
        }

        def x(xpathexpr, root = self.doc):
            return root.xpath(xpathexpr, namespaces=ns)

        def t(xpathexpr, root = self.doc):
            r = x(xpathexpr, root)
            if len(r) > 0:
                return r[0]
            return None

        def m(dict, *kv):
            """merge (k, v) pairs into dict if v is not None"""
            for (k, v) in kv:
                if v:
                    dict[k] = v
            return dict

        return m({ 
            'version' : t("//ss:version/text()"),
            'echoedQuery' : {
                'queryString' : t("//ss:echoedQuery/ss:queryString/text()"),
                'timeStamp' : t("//ss:echoedQuery/@timeStamp"),
                'library' : {
                    'name' : t("//ss:echoedQuery/ss:library/ss:name/text()"),
                    'id' : t("//ss:echoedQuery/ss:library/@id")
                }
            },
            'dbDate' : t("//ss:results/@dbDate"),
            'results' : [ {
                'format' : t("./@format", result),
                'citation' : m({ },
                    ('title', t(".//dc:title/text()")),
                    ('creator', t(".//dc:creator/text()")),
                    ('source', t(".//dc:source/text()")),
                    ('date', t(".//dc:date/text()")),
                    ('publisher', t(".//dc:publisher/text()")),
                    ('creatorFirst', t(".//ss:creatorFirst/text()")),
                    ('creatorMiddle', t(".//ss:creatorMiddle/text()")),
                    ('creatorLast', t(".//ss:creatorLast/text()")),
                    ('volume', t(".//ss:volume/text()")),
                    ('issue', t(".//ss:issue/text()")),
                    ('spage', t(".//ss:spage/text()")),
                    ('doi', t(".//ss:doi/text()")),
                    ('pmid', t(".//ss:pmid/text()")),
                    ('publicationPlace', t(".//ss:publicationPlace/text()")),
                    ('institution', t(".//ss:institution/text()")),
                    ('advisor', t(".//ss:advisor/text()")),
                    ('patentNumber', t(".//ss:patentNumber/text()")),
                    # assumes at most one ISSN per type
                    ('issn', dict([ (t("./@type", issn), t("./text()", issn))
                                   for issn in x("//ss:issn") ])),
                    ('isbn', [ t("./text()", isbn) for isbn in x("//ss:isbn") ])
                ),
                'linkGroups' : [ {
                    'type' : t("./@type", group),
                    'holdingData' : m({ 
                            'providerId' : t(".//ss:providerId/text()", group),
                            'providerName' : t(".//ss:providerName/text()", group),
                            'databaseId' : t(".//ss:databaseId/text()", group),
                            'databaseName' : t(".//ss:databaseName/text()", group),
                        },
                        # output normalizedData/startDate instead of startDate, 
                        # assuming that 'startDate' is redundant
                        ('startDate' , t(".//ss:normalizedData/ss:startDate/text()", group)),
                        ('endDate' , t(".//ss:normalizedData/ss:endDate/text()", group))),
                    # assumes at most one URL per type
                    'url' : dict([ (t("./@type", url), t("./text()", url)) 
                                   for url in x("./ss:url", group) ])
                } for group in x("//ss:linkGroups/ss:linkGroup")]
            } for result in x("//ss:result") ] }, 
            # optional
            ('diagnostics', 
                [ m({ 'uri' : t("./sd:uri/text()", diag) },
                    ('details', t("./sd:details/text()", diag)), 
                    ('message', t("./sd:message/text()", diag))
                ) for diag in x("//sd:diagnostic")]
            )
            # TBD derivedQueryData
        )
        
#Brown additions
#Make the OpenURL for passing on. 
SERSOL_MAP = {
    'journal': {
        'title': 'title',
        'creatorLast': 'aulast',
        'creator': 'au',
        'creatorFirst': 'aufirst',
        'creatorMiddle': 'auinitm',
        'source': 'jtitle',
        'date': 'date',
        #issns are tricky - handle in application logic
        'issn': 'issn',
        'eissn': 'eissn',
        'isbn': 'isbn',
        'volume': 'volume',
        'issue': 'issue',
        'spage': 'spage',
        #dois and pmids need to be handled differently too.
        #This mapping is here just to retain their original keys.
        'doi': 'doi',
        'pmid': 'pmid',
        #'publisher': 'publisher'
        #publicationPlace
        },
    'book': {
        'publisher': 'pub',
        'isbn': 'isbn',
        'title': 'btitle',
        'date': 'date',
        'creator': 'author',
        'creatorLast': 'aulast',
        'creatorLast': 'aulast',
        'creatorFirst': 'aufirst',
        'creatorMiddle': 'auinitm',
        'isbn': 'isbn',
        'title': 'btitle',
        'date': 'date',
        'publicationPlace': 'place',
        'format': 'genre',
        'source': 'btitle',
    }
}
