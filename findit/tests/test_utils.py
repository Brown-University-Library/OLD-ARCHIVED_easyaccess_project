# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest
from findit.utils import make_illiad_url, BulSerSol
from py360link2.link360 import get_sersol_data
from django.conf import settings
from pprint import pprint

import urllib
import urlparse


class IlliadURLTests(unittest.TestCase):
    """
    To do.
    """
    def test_referrer(self):
        ourl = 'rft_id%3Dinfo%253Adoi%252F10.1603%252F0022-2585-38.3.446%26rft.atitle%3DToxic%2BEffect%2Bof%2BGarlic%2BExtracts%2Bon%2Bthe%2BEggs%2Bof%2B%2B%2B%2B%2B%2B%2B%2B%2B%2B%2B%2B%2B%2B%2528Diptera%253A%2BCulicidae%2529%253A%2BA%2BScanning%2BElectron%2BMicroscopic%2BStudy%26rft.issue%3D3%26rft.aulast%3DJarial%26rft.volume%3D38%26rft.jtitle%3DJournal%2Bof%2Bmedical%2Bentomology%26rft.aufirst%3DMohinder%26rft.date%3D2001-05%26rft.auinitm%3DS.%26rft.eissn%3D1938-2928%26rft.au%3DJarial%252C%2BMohinder%2BS.%26rft.spage%3D446%26rft.issn%3D0022-2585%26url_ver%3DZ39.88-2004%26version%3D1.0%26rft_val_fmt%3Dinfo%253Aofi%252Ffmt%253Akev%253Amtx%253Ajournal%26rft.genre%3Darticle'
        #with pmid
        ourl = 'rft.issn%3D0742-2822%26rft.au%3DDalby%20Kristensen%2C%20Steen%26rft.aulast%3DDalby%20Kristensen%26rft.volume%3D13%26rft.jtitle%3DEchocardiography%20(Mount%20Kisco%2C%20N.Y.)%26rft.aufirst%3DSteen%26rft.date%3D1996-07%26rft.atitle%3DRupture%20of%20Aortic%20Dissection%20During%20Attempted%20Transesophageal%20Echocardiography%26pmid%3D11442947%26rft_id%3Dinfo%3Apmid%2F11442947%26rft.eissn%3D1540-8175%26rft.issue%3D4%26rft.spage%3D405%26url_ver%3DZ39.88-2004%26version%3D1.0%26rft_val_fmt%3Dinfo%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal%26rft.genre%3Darticle'
        #dvd from oclc
        ourl = 'sid=FirstSearch:WorldCat&title=Einstein on the beach&date=1993&aulast=Glass&aufirst=Philip&id=doi:&pid=<accession number>29050194</accession number><fssessid>0</fssessid>&url_ver=Z39.88-2004&rfr_id=info:sid/firstsearch.oclc.org:WorldCat&rft_val_fmt=info:ofi/fmt:kev:mtx:book&req_dat=<sessionid>0</sessionid>&rfe_dat=<accessionnumber>29050194</accessionnumber>&rft_id=info:oclcnum/29050194&rft.aulast=Glass&rft.aufirst=Philip&rft.title=Einstein on the beach&rft.date=1993&rft.aucorp=Philip Glass Ensemble.&rft.place=New York, NY :&rft.pub=Elektra Nonesuch,&rft.genre=unknown'
        ourl = 'rfr_id%3DFirstSearch%253AWorldCat%26isbn%3D9780767853569%26title%3DA%2Bfew%2Bgood%2Bmen%26date%3D2001%26aulast%3DReiner%26aufirst%3DRob%26id%3Ddoi%253A%26pid%3D%253Caccession%2Bnumber%253E47247051%253C%252Faccession%2Bnumber%253E%253Cfssessid%253E0%253C%252Ffssessid%253E%26url_ver%3DZ39.88-2004%26rfr_id%3Dinfo%253Asid%252Ffirstsearch.oclc.org%253AWorldCat%26rft_val_fmt%3Dinfo%253Aofi%252Ffmt%253Akev%253Amtx%253Abook%26req_dat%3D%253Csessionid%253E0%253C%252Fsessionid%253E%26rfe_dat%3D%253Caccessionnumber%253E47247051%253C%252Faccessionnumber%253E%26rft_id%3Dinfo%253Aoclcnum%252F47247051%26rft_id%3Durn%253AISBN%253A9780767853569%26rft.aulast%3DReiner%26rft.aufirst%3DRob%26rft.title%3DA%2Bfew%2Bgood%2Bmen%26rft.date%3D2001%26rft.isbn%3D9780767853569%26rft.aucorp%3DColumbia%2BPictures.%253BCastle%2BRock%2BEntertainment%2B%2528Firm%2529%253BColumbia%2BTriStar%2BHome%2BVideo%2B%2528Firm%2529%26rft.place%3DCulver%2BCity%252C%2BCA%2B%253A%26rft.pub%3DColumbia%2BTriStar%2BHome%2BVideo%252C%26rft.genre%3Dunknown%26checksum%3D065b7cc8e6abf86e89b5639ee3939c09&title=Brown+University&linktype=openurl&detail=RBN'
        ill = make_illiad_url(ourl)
        ill_dict = urlparse.parse_qs(ill)
        #pprint(ill_dict)
        self.assertTrue('FirstSearch:WorldCat' in ill_dict['sid'])

    def test_date(self):
        #Dates need to just be the four digit year.
        ourl = 'rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.auinitm=D&rft.spage=392&rft.au=Schlenker%2C+J+D&rft.aulast=Schlenker&sid=bul_easy_article&rft_id=info%3Apmid%2F7252116&rft.date=1981-07&rft.issn=0363-5023&rft.aufirst=J&rft.volume=6&version=1.0&url_ver=Z39.88-2004&rft.atitle=Three+complications+of+untreated+partial+laceration+of+flexor+tendon--entrapment%2C+rupture%2C+and+triggering&rft.eissn=1531-6564&pmid=7252116&rft.jtitle=The+Journal+of+hand+surgery+%28American+ed.%29&rft.issue=4&rft.genre=article'
        ill = make_illiad_url(ourl)
        ill_dict = urlparse.parse_qs(ill)
        date = ill_dict['rft.date'][0]
        self.assertEqual(date, '1981')

    def test_pmid(self):
        """
        Make sure the ILL url has the pubmed ID in the notes field.
        """
        ourl = 'rft.eissn=1531-6564&rft.aulast=Schlenker&rft.au=Schlenker%2C+J+D&rft.atitle=Three+complications+of+untreated+partial+laceration+of+flexor+tendon--entrapment%2C+rupture%2C+and+triggering&rft.volume=6&rft.jtitle=The+Journal+of+hand+surgery+%28American+ed.%29&rft.aufirst=J&rft.date=1981-07&rft.auinitm=D&rft.spage=392&rft.issue=4&pmid=7252116&rft_id=info%3Apmid%2F7252116&rft.issn=0363-5023&url_ver=Z39.88-2004&version=1.0&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal&rft.genre=article'
        ill = make_illiad_url(ourl)
        ill_dict = urlparse.parse_qs(ill)
        note = ill_dict['Notes'][0]
        self.assertTrue(note.rfind('7252116') > -1)

class LinkGroupTests(unittest.TestCase):
    """
    Test how the link groups returned by 360 links are parsed.
    """

    def _fetch(self, query):
        data = get_sersol_data(query, key=settings.BUL_LINK_SERSOL_KEY)
        resolved = BulSerSol(data)
        return resolved


    def test_vague_links(self):
        #ourl = "volume=9&genre=article&spage=39&sid=EBSCO:qrh&title=Gay+%26+Lesbian+Review+Worldwide&date=20020501&issue=3&issn=15321118&pid=&atitle=Chaste+Take+on+Those+Naughty+Victorian's."
        ourl = "rft.issn=0301-0066&rft.externalDocID=19806992&rft.date=2009-01-01&rft.volume=38&rft.issue=6&rft.spage=927&rft.jtitle=Perception&rft.au=Rhodes%2C+Gillian&rft.au=Jeffery%2C+Linda&rft.atitle=The+Thatcher+illusion%3A+now+you+see+it%2C+now+you+don%27t&ctx_ver=Z39.88-2004&rft.genre=article&ctx_enc=info%3Aofi%2Fenc%3AUTF-8&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal"
        data = get_sersol_data(ourl, key=settings.BUL_LINK_SERSOL_KEY)
        resolved = BulSerSol(data)
        access = resolved.access_points()
        self.assertTrue(access['has_vague_links'])
        self.assertEqual(access['online'][0]['type'], 'journal')
        self.assertEqual(access['print'], [])
        #pprint(resolved.access_points())

    def test_direct_link(self):
        """
        This is brittle.  If subscription changes.  This might not pass.
        """
        resolved = self._fetch("sid=google&auinit=T&aulast=SOTA&atitle=Phylogeny+and+divergence+time+of+island+tiger+beetles+of+the+genus+Cylindera+(Coleoptera:+Cicindelidae)+in+East+Asia&id=doi:10.1111/j.1095-8312.2011.01617.x&title=Biological+journal+of+the+Linnean+Society&volume=102&issue=4&date=2011&spage=715&issn=0024-4066")
        access = resolved.access_points()
        self.assertFalse(access['has_vague_links'])
        self.assertFalse(access['direct_link']['link'] is None, "Didn't get the expected direct link.")

    def test_print(self):
        """
        Need to create database fixture to test print resolving.
        """
        #ourl = "volume=9&genre=article&spage=39&sid=EBSCO:qrh&title=Gay+%26+Lesbian+Review+Worldwide&date=20020501&issue=3&issn=15321118&pid=&atitle=Chaste+Take+on+Those+Naughty+Victorian's."
        #resolved = self._fetch(ourl)
        #access = resolved.access_points()
        #pprint(access)
        #self.assertFalse(access['direct_link'])
        #self.assert


class CitationLinkerTests(unittest.TestCase):
    """
    Test the citation linker logic.
    """

    def _fetch(self, query):
        data = get_sersol_data(query, key=settings.BUL_LINK_SERSOL_KEY)
        resolved = BulSerSol(data)
        return resolved

    def test_citation_linker(self):
        #Start page only
        resolved = self._fetch('rft.spage=299&rft.volume=32&rft.issue=4&rft.aulast=El-Dib&SS_authors=El-Dib+M&rft.au=El-Dib+M&rft.title=Journal+of+Perinatology&SS_ReferentFormat=JournalFormat&citationsubmit=Look+Up&rft.aufirst=M&rft.atitle=Neurobehavioral+assessment+as+a+predictor+of+neurodevelopmental+outcome+in+preterm+infants&rft.genre=article&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal')
        citation_form = resolved.citation_form_dict()
        self.assertEqual(citation_form['pages'],
                         '299-EOA')
        #No pages.
        resolved = self._fetch('rft.volume=32&rft.issue=4&rft.aulast=El-Dib&SS_authors=El-Dib+M&rft.au=El-Dib+M&rft.title=Journal+of+Perinatology&SS_ReferentFormat=JournalFormat&citationsubmit=Look+Up&rft.aufirst=M&rft.atitle=Neurobehavioral+assessment+as+a+predictor+of+neurodevelopmental+outcome+in+preterm+infants&rft.genre=article&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal')
        citation_form = resolved.citation_form_dict()
        self.assertEqual(citation_form.get('pages', None), None)
        #Full page range - not supported at the moment since we are relying
        #on 360link data and it doesn't include end pages.




if __name__ == '__main__':
    unittest.main()
