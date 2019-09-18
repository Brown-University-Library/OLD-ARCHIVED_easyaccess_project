# -*- coding: utf-8 -*-

from django.contrib import admin
# from django.db import models
from bul_link.models import Resource


class ResourceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'shortlink', 'referrer']
    list_display = ['id', 'shortlink', 'truncated_item_json', 'date_created', 'date_modified']
    list_filter = ['referrer', 'date_created', 'date_modified']


    def truncated_item_json(self, obj):
        tij = 'init'
        if len( obj.item_json ) <= 50:
            tij = obj.item_json
        else:
            tij = f'{obj.item_json[0:47]}...'
        return tij

    def truncated_query(self, obj):
        tq = 'init'
        if len( obj.query ) < 30:
            tq = obj.query
        else:
            tq = f'{obj.query[0:27]}...'
        return tq
    # upper_case_name.short_description = 'Name'

    # def upper_case_name(self, obj):
    #     return ("%s %s" % (obj.first_name, obj.last_name)).upper()
    # upper_case_name.short_description = 'Name'

admin.site.register(Resource, ResourceAdmin)
