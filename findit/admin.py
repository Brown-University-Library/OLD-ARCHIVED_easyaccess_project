# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin
from models import PrintTitle, Request, UserMessage


class RequestAdmin(admin.ModelAdmin):
    search_fields = ['illiad_tn', 'user']
    list_display = ['item', 'user', 'illiad_tn', 'date_created', 'date_modified']
    list_filter = ['date_created']
    pass


# class UserProfileAdmin(admin.ModelAdmin):
#    search_fields = ['membership', 'barcode']
#    list_display = ['user', 'membership', 'date_created']
#    pass


class PrintTitleAdmin(admin.ModelAdmin):
    search_fields = ['issn', 'call_number', 'location', 'start', 'end', 'call_number']
    list_display = ['issn', 'start', 'end', 'location', 'call_number']
    list_filter = ['location']
    pass


class UserMessageAdmin(admin.ModelAdmin):
    search_fields = ['type', 'subject', 'text']
    list_display = ['type', 'subject']
    readonly_fields = ('date_created', 'date_modified')


admin.site.register(Request, RequestAdmin)
# admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(PrintTitle, PrintTitleAdmin)
admin.site.register(UserMessage, UserMessageAdmin)
