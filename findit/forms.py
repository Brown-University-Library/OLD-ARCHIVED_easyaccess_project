# -*- coding: utf-8 -*-

from __future__ import unicode_literals

#Types
#Article/Journal
#Book
#Dissertation
#Patent
#
#Common to all
#DOI
#rft.title - patent/dissertation labeling varies
from django import forms


def _short(label):
    """Helper for creating a short char form field."""
    return forms.CharField(max_length=20,
                           label=label,
                           required=False,)
def _medium(label):
    """Helper for creating a medium char form field."""
    return forms.CharField(max_length=100,
                           label=label,
                           required=False,)
def _long(label):
    """Helper for creating a long char form field."""
    return forms.CharField(max_length=250,
                             label=label,
                             required=False)

ARTICLE_GENRE_CHOICES = (
                         ('article', 'Article'),
                         ('conference', 'Conference'),
                         ('issue', 'Issue'),
                         ('preprint', 'Preprint'),
                         ('proceeding', 'Proceeding'),
                         ('report', 'Report'),
                         ('unknown', 'Unknown'),
)

BOOK_GENRE_CHOICES = (
                         ('book', 'Book'),
                         ('bookitem', 'Chapter/Book Item'),
                         ('conference', 'Conference'),
                         ('document', 'Document'),
                         ('proceeding', 'Proceeding'),
                         ('report', 'Report'),
                         ('unknown', 'Unknown'),
)


class ArticleForm(forms.Form):
    #genre = forms.ChoiceField(choices=ARTICLE_GENRE_CHOICES,
    #                          required=False)
    atitle = _long("Article Title *")
    jtitle = _long("Journal Title *")
    pages = _short('Pages *')
    date = _short('Date *')
    issn = _short("ISSN")
    id = _medium('DOI')
    pmid = _short('PMID')
    volume = _short('Volume')
    issue = _short('Issue')
    #spage = _short('Start page')
    #epage = _short('End page')
    au = _long("Author")
    #aulast = _long("Author (last)")
    #aufirst = _long("Author (first)")
    rfe_dat = _medium("OCLC number")


    def _cleaner(self, values):
        as_string = ','.join([v for v in values])
        return as_string.lstrip(',')

    def clean_issn(self):
        data = self.cleaned_data['issn']
        data = self._cleaner(data)
        #if not data:
        #    raise forms.ValidationError("An ISSN is required.")
        return data

    def clean_genre(self):
        data = self.cleaned_data['genre']
        return self._cleaner(data)


class BookForm(forms.Form):
    #genre = forms.ChoiceField(choices=BOOK_GENRE_CHOICES,
    #                      required=False)
    btitle = _long("Title *")
    id = _medium('DOI')
    isbn = _short("ISBN")
    date = _short('Date *')
    au = _long("Author")
    #aufirst = _long("Author (first)")
    #aulast = _long("Author (last)")
    pub = _long('Publisher')
    place = _long('Place')
    pages = _short('Pages')
    spage = _short('Start page')
    epage = _short('End page')
    rfe_dat = _medium("OCLC number")


class DissertationForm(forms.Form):
    title = _long("Dissertation")
    isbn = _short("ISBN")
    id = _medium('DOI')
    inst = _long("Institution")
    date = _short('Date')
    au = _long("Author (full)")
    aufirst = _long("Author (first)")
    aulast = _long("Author (last)")
    advisor = _long("Advisor")
    rfe_dat = _medium("OCLC number")

class PatentForm(forms.Form):
    title = _long("Patent")
    id = _medium('DOI')
    number = _long('Patent #')
    pubdate = _short('Pub. Date')
    date = _short('Date')
    au = _long("Author (full)")
    advisor = _long("Advisor")
    inventor = _long("Inventor")
    invlast = _long("Inventor (last name)")
    invfirst = _long("Inventor (first)")
    rfe_dat = _medium("OCLC number")


