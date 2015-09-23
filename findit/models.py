import json, os
from django.db import models
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.core.mail import send_mail

from bul_link.models import Resource

class PrintTitle(models.Model):
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
    user = models.ForeignKey(User)
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


#class UserProfile(models.Model):
#    # This field is required.
#    user = models.OneToOneField(User)
#    # Other fields here
#    barcode = models.CharField(max_length=25, blank=True, null=True, default=None)
#    is_faculty = models.BooleanField(default=False)
#    is_student = models.BooleanField(default=False)
#    is_staff = models.BooleanField(default=False)
#    #More granular status pulled from Shib headers
#    membership = models.CharField(max_length=25, blank=True, null=True, default='unknown')
#    #http://djangosnippets.org/snippets/1017/
#    date_created = models.DateTimeField()
#    date_modified = models.DateTimeField()
#
#    def save(self, *args, **kwargs):
#        if self.date_created == None:
#            self.date_created = datetime.now()
#        self.date_modified = datetime.now()
#        super(UserProfile, self).save()
#
#    def primary_affiliation(self):
#        """
#        Used for the Illiad registration piece.  Will attempt to populate
#        with information from the membership field.  If not, will return
#        the first valid affiliation.
#        """
#        if self.membership != 'unknown':
#            return self.membership
#        if self.is_faculty == True:
#            return "Faculty"
#        elif self.is_staff == True:
#            return "Staff"
#        elif self.is_student == True:
#            return "Student"
#        else:
#            return "Unknown"
#
#    def can_request_print(self):
#        """
#        Helper for determine if a user can request print document
#        delivery for locally held items.
#        """
#        if self.is_faculty is True:
#            return True
#        if "medical" in self.membership.lower():
#            return True
#        return False
#
#    def illiad(self):
#        d = {}
#        d['username'] = self.user.username.replace('@brown.edu', '')
#        d['first_name'] = self.user.first_name
#        d['last_name'] = self.user.last_name
#        d['email'] = self.user.email
#        #Set status.
#        d['status'] = self.primary_affiliation()
#        return d
#
#    def __unicode__(self):
#        return "%s" % self.user.username






