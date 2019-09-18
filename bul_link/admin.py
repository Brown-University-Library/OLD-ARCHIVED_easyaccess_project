# -*- coding: utf-8 -*-

from django.contrib import admin
# from django.db import models
from bul_link.models import Resource


class ResourceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'referrer']
    list_display = ['id', 'referrer', 'truncated_query', 'date_created', 'date_modified']
    list_filter = ['referrer', 'date_created', 'date_modified']
    pass

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
