# -*- coding: utf-8 -*-

from __future__ import unicode_literals

# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from datetime import datetime
from django.db import models


class EasyBorrowRequest(models.Model):
    # id = models.IntegerField(primary_key=True, editable=False)  # if this is enabled, instance will not return id/pk
    title = models.CharField(max_length=765, default='')
    isbn = models.CharField(max_length=39, default='')
    wc_accession = models.IntegerField(default=0)
    bibno = models.CharField(max_length=24, default='')
    pref = models.CharField(max_length=15, default='quick')
    loc = models.CharField(max_length=12, default='rock')
    alt_edition = models.CharField(max_length=3, default='y')
    volumes = models.CharField(max_length=90, default='')
    sfxurl = models.TextField()
    patronid = models.IntegerField(db_column='patronId', default=0) # Field name made lowercase.
    eppn = models.CharField(max_length=20, default='unknown')
    name = models.CharField(max_length=765, default='')
    firstname = models.CharField(max_length=360, default='')
    lastname = models.CharField(max_length=360, default='')
    created = models.DateTimeField(default=None)
    barcode = models.CharField(max_length=42, default='')
    email = models.CharField(max_length=150, default='')
    group = models.CharField(max_length=60, default='')
    staffnote = models.CharField(max_length=765, default='')
    request_status = models.CharField(max_length=90, default='not_yet_processed')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        # managed = False
        db_table = u'requests'

"""
For reference, sqlit3 syntax for creating this table:

CREATE TABLE IF NOT EXISTS `requests` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `title` varchar(255) NOT NULL DEFAULT '',
  `isbn` varchar(13) NOT NULL DEFAULT '',
  `wc_accession` int(20) NOT NULL DEFAULT '0',
  `bibno` varchar(8) NOT NULL DEFAULT '',
  `pref` varchar(8) NOT NULL DEFAULT 'quick',
  `loc` varchar(8) NOT NULL DEFAULT 'rock',
  `alt_edition` varchar(8) NOT NULL DEFAULT 'y',
  `volumes` varchar(30) NOT NULL DEFAULT '',
  `sfxurl` text NOT NULL,
  `patronId` int(11) NOT NULL DEFAULT '0',
  `name` varchar(255) NOT NULL DEFAULT '',
  `firstname` varchar(120) NOT NULL DEFAULT '',
  `lastname` varchar(120) NOT NULL DEFAULT '',
  `created` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `barcode` varchar(14) NOT NULL DEFAULT '',
  `email` varchar(50) NOT NULL DEFAULT '',
  `group` varchar(20) NOT NULL DEFAULT '',
  `staffnote` varchar(255) NOT NULL DEFAULT '',
  `request_status` varchar(30) NOT NULL DEFAULT 'not_yet_processed',
  `eppn` varchar(20) NOT NULL DEFAULT 'init'
);
"""
