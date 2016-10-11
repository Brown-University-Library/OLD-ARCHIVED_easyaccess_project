
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint
# from delivery import app_settings
from delivery.classes.login_helper import LoginViewHelper
from django.test import TestCase


log = logging.getLogger('access')
# TestCase.maxDiff = None


class LoginViewHelperTest(TestCase):
    """ Checks LoginViewHelper() """

    def setUp(self):
        self.helper = LoginViewHelper()

    def test_check_querystring_good_data(self):
        """ Good querystring should return same value. """
        initial_querystring = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9789570810530&title=Xu+Jiatun+Xianggang+hui+yi+lu&date=1993&aulast=Xu&aufirst=Jiatun&id=doi%3A&pid=29972077%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3EChu+ban.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E29972077%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F29972077&rft_id=urn%3AISBN%3A9789570810530&rft.aulast=Xu&rft.aufirst=Jiatun&rft.btitle=Xu+Jiatun+Xianggang+hui+yi+lu&rft.date=1993&rft.isbn=9789570810530&rft.place=Xianggang++%3BTaibei+Shi&rft.pub=Xianggang+lian+he+bao+you+xian+gong+si+%3B%3BZong+jing+xiao+Lian+jing+chu+ban+shi+ye+gong+si&rft.edition=Chu+ban.&rft.genre=book'
        updated_querystring = self.helper.check_querystring( initial_querystring )
        self.assertEqual( updated_querystring, initial_querystring )

    def test_check_querystring_bad_data(self):
        """ Truncated querystring should not end in partially-encoded word. """
        initial_querystring = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9788479590482&title=Eucarist%C3%ADa+y+nueva+evangelización+%3A+actas+del+IV+Simposio+la+Iglesia+en+España+y+América%3A+siglos+XVI-XX+%3A+celebrado+en+Sevilla+el+30+de+abril+de+1993&date=1994&aulast=Castañeda+Delgado&aufirst=Paulino&id=doi%3A&pid=39465160%3Cfssessid%3E0%3C%2Ffssessid%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E39465160%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F39465160&rft_id=urn%3AISBN%3A9788479590482&rft.aulast=Castañeda+Delgado&rft.aufirst=Paulino&rft.btitle=Eucarist%C3%ADa+y+nueva+evangelización+%3A+actas+del+IV+Simposio+la+Iglesia+en+España+y+América%3A+siglos+XVI-XX+%3A+celebrado+en+Sevilla+el+30+de+abril+de+1993&rft.date=1994&rft.isbn=9788479590482&rft.aucorp=Simposio+de+la+Iglesia+en+España+y+América%3A+siglos%2'
        expected_updated_querystring = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9788479590482&title=Eucarist%C3%ADa+y+nueva+evangelización+%3A+actas+del+IV+Simposio+la+Iglesia+en+España+y+América%3A+siglos+XVI-XX+%3A+celebrado+en+Sevilla+el+30+de+abril+de+1993&date=1994&aulast=Castañeda+Delgado&aufirst=Paulino&id=doi%3A&pid=39465160%3Cfssessid%3E0%3C%2Ffssessid%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E39465160%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F39465160&rft_id=urn%3AISBN%3A9788479590482&rft.aulast=Castañeda+Delgado&rft.aufirst=Paulino&rft.btitle=Eucarist%C3%ADa+y+nueva+evangelización+%3A+actas+del+IV+Simposio+la+Iglesia+en+España+y+América%3A+siglos+XVI-XX+%3A+celebrado+en+Sevilla+el+30+de+abril+de+1993&rft.date=1994&rft.isbn=9788479590482&rft.aucorp=Simposio+de+la+Iglesia+en+España+y+América%3A+siglos'
        self.assertEqual( expected_updated_querystring, self.helper.check_querystring( initial_querystring ) )

    def test_check_querystring_bad_data_2(self):
        """ Truncated querystring should not end in partially-encoded word; another example. """
        initial_querystring = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9789948220855&title=Houses+of+God+%3A+from+the+Great+Mosque+of+Qayrawan+to+the+Sheikh+Zayed+Grand+Mosque+%3D+Baywtullāh+min+Jāmiʻ+al-Qayrawān+ilī+Jāmiʻ+al-Shaykh+Zāyid+al-Kabīr&date=2014&aulast=Shaikh&aufirst=Khalil&id=doi%3A&pid=948967938%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3EFirst+edition.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E948967938%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F948967938&rft_id=urn%3AISBN%3A9789948220855&rft.aulast=Shaikh&rft.aufirst=Khalil&rft.btitle=Houses+of+God+%3A+from+the+Great+Mosque+of+Qayrawan+to+the+Sheikh+Zayed+Grand+Mosque+%3D+Baywtullāh+min+Jāmiʻ+al-Qayrawān+ilī+Jāmiʻ+al-Shaykh+Zāyid+al-Kabīr&rft.date=2014&rft.isbn=9789948220855&rft.aucorp=Jāmiʻ+al-Shaykh+Zāyid+al-Kabīr+%28Abū+Ẓaby%2C+United+Arab+Emirates%29%2C%3BAbū+Z%'
        expected_updated_querystring = 'sid=FirstSearch%3AWorldCat&genre=book&isbn=9789948220855&title=Houses+of+God+%3A+from+the+Great+Mosque+of+Qayrawan+to+the+Sheikh+Zayed+Grand+Mosque+%3D+Baywtullāh+min+Jāmiʻ+al-Qayrawān+ilī+Jāmiʻ+al-Shaykh+Zāyid+al-Kabīr&date=2014&aulast=Shaikh&aufirst=Khalil&id=doi%3A&pid=948967938%3Cfssessid%3E0%3C%2Ffssessid%3E%3Cedition%3EFirst+edition.%3C%2Fedition%3E&url_ver=Z39.88-2004&rfr_id=info%3Asid%2Ffirstsearch.oclc.org%3AWorldCat&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&req_dat=%3Csessionid%3E0%3C%2Fsessionid%3E&rfe_dat=%3Caccessionnumber%3E948967938%3C%2Faccessionnumber%3E&rft_id=info%3Aoclcnum%2F948967938&rft_id=urn%3AISBN%3A9789948220855&rft.aulast=Shaikh&rft.aufirst=Khalil&rft.btitle=Houses+of+God+%3A+from+the+Great+Mosque+of+Qayrawan+to+the+Sheikh+Zayed+Grand+Mosque+%3D+Baywtullāh+min+Jāmiʻ+al-Qayrawān+ilī+Jāmiʻ+al-Shaykh+Zāyid+al-Kabīr&rft.date=2014&rft.isbn=9789948220855&rft.aucorp=Jāmiʻ+al-Shaykh+Zāyid+al-Kabīr+%28Abū+Ẓaby%2C+United+Arab+Emirates%29%2C%3BAbū+Z'
        self.assertEqual( expected_updated_querystring, self.helper.check_querystring( initial_querystring ) )

    # end LoginViewHelperTest()
