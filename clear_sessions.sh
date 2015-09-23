#!/bin/sh
#clear django_session table
cd ..
DJANGO_SETTINGS_MODULE="easy_article.settings" \
python -c 'from django.contrib.sessions.models import Session; \
      Session.objects.all().delete()' 

