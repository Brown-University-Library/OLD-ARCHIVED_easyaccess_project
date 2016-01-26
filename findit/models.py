# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, os
from datetime import datetime

from bul_link.models import Resource
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models


class PrintTitle(models.Model):
    """ Stores data from file produced by rapid.
        See <https://github.com/birkin/rapid_exports/blob/5bb05dda389113661703bb682c9542b4599a9566/rapid_app/views.py#L24> """
    key = models.CharField(max_length=20, primary_key=True)
    issn = models.CharField(max_length=15)
    start = models.IntegerField()
    end = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=25, blank=True, null=True)
    call_number = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return "%s %s to %s" % (self.issn, self.start, self.end)


class Request(models.Model):
    item = models.ForeignKey(Resource)
    # user = models.ForeignKey(User)
    user = models.OneToOneField(User)  # <http://deathofagremmie.com/2014/05/24/retiring-get-profile-and-auth-profile-module/>
    illiad_tn = models.CharField(max_length=25, blank=True, null=True)
    #http://djangosnippets.org/snippets/1017/
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.date_created == None:
            self.date_created = datetime.now()
        self.date_modified = datetime.now()
        super(Request, self).save()
        #send a message to admin
        send_mail("easyA request %s" % self.illiad_tn,
              "Illiad TN: %s\n\nUser:%s\n\nReferrer:%s\n\nURL:http://library.brown.edu/easyarticle/?%s\n" %\
                    (self.illiad_tn,
                     self.user.username.rstrip('@brown.edu'),
                     self.item.referrer,
                     self.item.query),
              os.environ['EZACS__FINDIT_MODELS_REQUEST_MAIL_FROM'],
              json.loads( os.environ['EZACS__FINDIT_MODELS_REQUEST_MAIL_TO_JSON'] ),
              fail_silently=False)

    def __unicode__(self):
        return "%s-%s" % (self.item, self.user)


MESSAGE_TYPE_CHOICES = (
    ('blocked','blocked'),
    ('confirmation','confirmation'),
)

helper = """
This will be the body of the message.  Confirmation emails will be followed by
the permanent link to the requested article.
"""


class UserMessage(models.Model):
    type = models.CharField(max_length=30, choices=MESSAGE_TYPE_CHOICES)
    subject = models.CharField(max_length=50, help_text="Email subject.")
    text = models.TextField(help_text=helper)

    date_created = models.DateTimeField(editable=False)
    date_modified = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if self.date_created == None:
            self.date_created = datetime.now()
        self.date_modified = datetime.now()
        super(UserMessage, self).save()

    def __unicode__(self):
        return "%s" % (self.type)
