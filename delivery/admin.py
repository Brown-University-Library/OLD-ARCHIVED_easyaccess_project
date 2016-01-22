# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin
from easyborrow_models import EasyBorrowRequest
from models import Resource, Request, UserMessage, LibraryProfile


class MultiDBModelAdmin(admin.ModelAdmin):
    # A handy constant for the name of the alternate database.
    using = 'ezborrow'

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super(MultiDBModelAdmin, self).queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super(MultiDBModelAdmin, self).formfield_for_foreignkey(db_field, request=request, using=self.using, **kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super(MultiDBModelAdmin, self).formfield_for_manytomany(db_field, request=request, using=self.using, **kwargs)

class EzbRequestAdmin(MultiDBModelAdmin):
    #pass
    search_fields = ['id', 'patronid']
    list_display = ['id', 'patronid', 'request_status' ]
    #list_filter = ['request_status']
#ezb = admin.Site('ezborrow')
admin.site.register(EasyBorrowRequest, EzbRequestAdmin)

#Local models
class RequestAdmin(admin.ModelAdmin):
    search_fields = ['transaction_number', 'user__last_name', 'user__first_name', 'user__username']
    list_display = ['item', 'user', 'transaction_number', 'date_created', 'date_modified']
    list_filter = ['date_created']
    pass
admin.site.register(Request, RequestAdmin)

class ResourceAdmin(admin.ModelAdmin):
    search_fields = ['id', 'referrer']
    list_display = ['id', 'referrer', 'date_created', 'date_modified']
    list_filter = ['referrer', 'date_created', 'date_modified']
    pass
admin.site.register(Resource, ResourceAdmin)

class UserMessageAdmin(admin.ModelAdmin):
    search_fields = ['type', 'subject', 'text']
    list_display = ['type', 'subject']
    readonly_fields=('date_created', 'date_modified')
admin.site.register(UserMessage, UserMessageAdmin)

class LibraryProfileAdmin(admin.ModelAdmin):
    search_fields = ['membership', 'barcode', 'user__last_name', 'user__username', 'user__first_name']
    list_display = ['user', 'membership', 'date_created']
admin.site.register(LibraryProfile, LibraryProfileAdmin)
