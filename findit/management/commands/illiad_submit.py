# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Handle Illiad registration.
"""
#django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
#stdlib
from optparse import make_option
import sys

#local
from findit.app_settings import ILLIAD_REMOTE_AUTH_URL, ILLIAD_REMOTE_AUTH_HEADER
from illiad.account import IlliadSession


class Command(BaseCommand):
    help = "For submitting ILLiad findit database."

    def handle(self, **options):
        from findit.models import Request
        new_requests = Request.objects.filter(illiad_tn='new')
        for request in new_requests:
            print request.user, request.id
