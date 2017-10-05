
### easy_access

on this page
- overview
- article flow
- book flow
- acknowledgements

---

#### overview

This repository contains code for a project of the [Brown University Library](http://library.brown.edu) to make getting articles and books easier.

It contains code for the web pages users see when they click links for articles and books which contain an [OpenUrl](https://en.wikipedia.org/wiki/OpenURL).

It also contains code for the handling of article-delivery (easyArticle); for books easyAccess (invisibly to the user) hands off to an [easyBorrow](https://github.com/birkin/easyborrow_controller) project.

easyAccess is, essentially, the Library's OpenUrl link-resolver, using, behind-the-scenes, the [SerialsSolutions 360Link api](http://www.proquest.com/products-services/discovery-services/360-Link.html).

---

#### article flow

- from information in the openurl, the item is determined to be an article, and all subsequent pages the user sees will be branded 'easyArticle'

- a check is made on the openurl to see if the item is specifically for a journal (as opposed to an article). This is rarely the case, but if so, the openurl request is redirected to Brown's 'search.serialssolutions.com' url. This is old inherited logic; we could likely improve this.

- if still in flow (almost always the case), a check is made on a Brown's 360Link 'openurl.xml.serialssolutions.com' api
    - if a direct link to full-text is found, easyAccess used to take the user right to that url, but a decision was made to instead have the user land at an easyArticle page showing all links to full text
        - there is some logic that affects the order links are shown, based on librarians defining which sources are better than others
        - note: all serialsolutions online links begin with `https://login.revproxy.brown.edu/login?url=the_destination_url` which triggers shib login
        - if the user has clicked a link from new-josiah to get to easyAccess, that openurl may contain an EDS full-text link. If so, that link is also listed after the other full-text links.
    - if a direct link to full-text is not found, but the 360link api indicates we have electronic access to that issue of the journal, the user lands at a page with a link to the journal and a note that the article _is_ available online, but that the link is not directly to the article, and some additional searching will be required on the publisher's website
    - if the 360link api lookup shows that we have the article in print, that information will appear on the landing page, whether or not there are also online links
    - if the 360link api has no online link information about the item, and no print information about the item, the user lands at a page with a link to 'Request from another library'

- if still in flow, and the user clicks the 'Request from another library' link, a confirmation 'Submit' button appears; if clicked, the request is submitted to [ILLiad](https://www.atlas-sys.com/illiad/) (our interlibary-loan service) on behalf of the user, and the user receives a confirmation email with tracking info.

- see 'Article Examples' on the [easyAccess home page](https://library.brown.edu/easyaccess/find/)

---

#### book flow

- from information in the openurl, the item is determined to be a book, and all subsequent pages the user sees will be branded 'easyBorrow'

- a background lookup is done to see if we have it, in a circulating location, or have a similar copy

- if we have the exact book, in a circulating location, the user is shown a page to that effect, with a link to the catalog record for the book

- if we have an alternate version (say, an ebook), but not the exact book the user has requested, the user is shown a page to that effect, with catalog links to the alternate versions, as well as a 'Request via easyBorrow' button for the specific book the user is looking for

- if the user clics the 'Request via easyBorrow' button, info about the book, the patron, and the request is temporarily stored in a db

- separate easyBorrow code detects the new request, and, depending on a few factors:
    - searches for the book in [BorrowDirect](http://www.borrowdirect.org) (our consortial loan partner), and requests it for the user if it's available
    - submits the request to ILLiad for the user if necessary

- see 'Book Examples' on the [easyAccess home page](https://library.brown.edu/easyaccess/find/)

---

#### acknowledgements

Not shown in the commit history is the fact that this entire project was implemented by [Ted Lawless](https://github.com/lawlesst) from 2012 through 2015. It has made the work of thousands of Brown University students and faculty vastly easier.

---
