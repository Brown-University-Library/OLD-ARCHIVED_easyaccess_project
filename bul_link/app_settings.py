from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

SERSOL_KEY = getattr(settings, 'BUL_LINK_SERSOL_KEY', None)

if SERSOL_KEY is None:
     raise ImproperlyConfigured('The link360 app requires a valid SERSOL_KEY')

SERSOL_TIMEOUT = getattr(settings, 'BUL_LINK_SERSOL_TIMEOUT', 30)
 
PERMALINK_PREFIX = getattr(settings, 'BUL_LINK_PERMALINK_PREFIX', 'bL')

CACHE_TIMEOUT = getattr(settings, 'BUL_LINK_CACHE_TIMEOUT', 60)

#These keys will be skipped when creating the cache key for resolved urls.
QUERY_SKIP_KEYS = ['csrfmiddlewaretoken', #redirects from forms
                    'rfr_id',
                    'paramdict',
                    'sid', 
                    'output' #internal output format specifier
                    ]

skip_keys = getattr(settings, 'BUL_LINK_QUERY_SKIP_KEYS', [])
QUERY_SKIP_KEYS.extend(skip_keys)


