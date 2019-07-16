# -*- coding: utf-8 -*-

from django.contrib import admin
# from django.db import models
from bul_link.models import Resource


class ResourceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'referrer']
    list_display = ['id', 'referrer', 'date_created', 'date_modified']
    list_filter = ['referrer', 'date_created', 'date_modified']
    pass

admin.site.register(Resource, ResourceAdmin)
