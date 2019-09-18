import logging

from django.db import models


log = logging.getLogger(__name__)


class Resource( models.Model ):

    query = models.TextField()
    referrer = models.CharField(max_length=200, blank=True, null=True)
    date_created = models.DateTimeField( auto_now_add=True )
    date_modified = models.DateTimeField( auto_now=True )

    item_json = models.TextField( default='{}' )
    patron_json = models.TextField( default='{}' )

    def save(self, *args, **kwargs):
        pass
        super( Resource, self ).save()

    # @models.permalink
    # def get_absolute_url(self):
    #     tiny = base62.from_decimal(self.id)
    #     return ('bul_link:permalink_view', (),
    #             {'tiny': tiny})

    def __unicode__(self):
        return self.id
