# -*- coding: utf-8 -*-

""" STILL USED? """

from datetime import datetime

from .app_settings import PERMALINK_PREFIX
from .baseconv import base62
from django.db import models
from django.db.models.signals import pre_save


class Resource(models.Model):
    query = models.TextField()
    referrer = models.CharField(max_length=200, blank=True, null=True)
    #http://djangosnippets.org/snippets/1017/
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.date_created == None:
            #These are new objects
            self.date_created = datetime.now()
        self.date_modified = datetime.now()
        super(Resource, self).save()

    @models.permalink
    def get_absolute_url(self):
        tiny = base62.from_decimal(self.id)
        return ('bul_link:permalink_view', (),
                {'tiny': tiny})


    def __str__(self):
        return str( self.id )
