# -*- coding: utf-8 -*-

from __future__ import unicode_literals

# def login_link(request):
#     from app_settings import LOGIN_URL
#     import urllib
#     encoded_path = urllib.quote(request.get_full_path())
#     ll = "%s?target=%s" % (LOGIN_URL,
#                          encoded_path)
#     return { 'login_link': ll }

def debug_mode(request):
    from app_settings import DEBUG
    return {'debug_mode': DEBUG}

