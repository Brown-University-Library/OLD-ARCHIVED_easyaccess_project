# from django.conf.urls.defaults import patterns, include, url
from django.conf.urls import include, url
from django.contrib import admin


admin.autodiscover()


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^user/', include('shibboleth.urls', namespace='shibboleth')),
    url(r'^borrow/', include('delivery.urls', namespace='delivery')),
    url(r'', include('findit.urls', namespace='findit')),
    #These are here just to register the namespace.  All links will be handled
    #by the above.
    url(r'', include('bul_link.urls', namespace='bul_link')),
    ]

# urlpatterns = patterns('',
#     url(r'^admin/', include(admin.site.urls)),
#     url(r'^user/', include('shibboleth.urls', namespace='shibboleth')),
#     url(r'^borrow/', include('delivery.urls', namespace='delivery')),
#     url(r'', include('findit.urls', namespace='findit')),
#     #These are here just to register the namespace.  All links will be handled
#     #by the above.
#     url(r'', include('bul_link.urls', namespace='bul_link')),
# )

# from django.conf.urls.defaults import *
#For 500 errors
handler500 = 'findit.views.server_error'
handler500 = 'findit.views.server_error'
