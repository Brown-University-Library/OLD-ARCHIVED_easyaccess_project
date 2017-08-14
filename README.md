
### easy_access

on this page
- overview
- article flow
- book flow
- acknowledgements

---

##### overview

This repository contains code for a project of the [Brown University Library](http://library.brown.edu) to make getting articles and books easier.

It contains code for the web pages users see when they click links for articles and books which contain an [OpenUrl](https://en.wikipedia.org/wiki/OpenURL).

It also contains code for the handling of article-delivery (easyArticle); for books it hands off to an [easyBorrow](https://github.com/birkin/easyborrow_controller) project.

---

##### article flow

- from information in the openurl, the item is determined to be an article, and all subsequent pages the user sees will be branded 'easyArticle'

- if the referrer is not on a 'skip summon check' list, and if there is a doi or pmid identifier, the [summon api](https://api.summon.serialssolutions.com/help/api/) is checked

- if summon is checked...
    - if the results contain a direct link the user is taken to the 'brown.summon.serialssolutions.com' full link to the article text (which triggers a shib login)

- if still in flow, a check is made on the openurl to see if the item is specifically for a journal. If so, the openurl request is redirected to Brown's 'search.serialssolutions.com' url

- if still in flow, a check is made on a Brown's [360Link](http://www.proquest.com/libraries/academic/discovery-services/360-Link.html) 'openurl.xml.serialssolutions.com' api
    - if a direct link to full-text is found, easyAccess _used_ to take the user right to that url, but a decision was made to instead have the user land at an easyArticle page showing all links to full text
        - note: all serialsolutions fulltext links begin with `https://login.revproxy.brown.edu/login?url=the_destination_url` which triggers shib login
    - if a direct link to full-text is not found, but 360link indicates we have electronic access to that issue of the journal, the user lands at a page with a link to the journal and a note that the article _is_ available online, but that the link is not directly to the article, and some additional searching will be required on the publisher's website
    - if there is no link to full-text or close to it, the user lands at a page with a link to 'Request from another library'

- if still in flow, and the user clicks the 'Request from another library' link, a confirmation 'Submit' button appears; if clicked, the request is submitted to ILLiad on behalf of the user.

---

##### book flow

- from information in the openurl, the item is determined to be a book, and all subsequent pages the user sees will be branded 'easyBorrow'

- a background lookup is done to see if we have it, in a circulating location, or have a similar copy

- if we have the exact book, in a circulating location, the user is shown a page to that effect, with a link to the catalog record for the book

- if we have an alternate version (say, an ebook), but not the exact book the user has requested, the user is shown a page to that effect, with catalog links to the alternate versions, as well as a 'Request via easyBorrow' button for the specific book the user is looking for

- if the user clics the 'Request via easyBorrow' button, info about the book, the patron, and the request is temporarily stored in a db

- separate easyBorrow code detects the new request, and, depending on a few factors:
    - searches for the book in [BorrowDirect](http://www.borrowdirect.org) (our consortial loan partner), and requests it for the user if it's available
    - submits the request to [ILLiad](https://www.atlas-sys.com/illiad/) (our interlibary-loan service) for the user if necessary

---

##### acknowledgements

Not shown in the commit history is the fact that this entire project was implemented by [Ted Lawless](https://github.com/lawlesst) from 2012 through 2015. It has made the work of thousands of Brown University students and faculty vastly easier.

---
