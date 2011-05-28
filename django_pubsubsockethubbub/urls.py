import os
from django.conf.urls.defaults import *
from django.conf import settings
#from django.contrib import admin
#admin.autodiscover()

from pubsubsockethubbub.views import socketio

urlpatterns = patterns('',
    url(r'', include('pubsubsockethubbub.urls')),
#    (r'^admin/', include(admin.site.urls)),
)

print "in urls"
