#import os
from django.conf.urls.defaults import patterns, include, url
#from django.conf import settings
from views import socketio

#urlpatterns = patterns('',
#    (r'^$', 'django.views.generic.simple.direct_to_template', {'template': 'chat.html'}),
#    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
#                {'document_root': os.path.join(settings.BASE_PATH, 'media')}),
#)

#urlpatterns += patterns('views',
#    (r'^socket\.io', 'socketio'),
#)

urlpatterns = patterns('',
    url(r'^socket\.io', socketio, name='socketio'),
)

#from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#urlpatterns += staticfiles_urlpatterns()

print "in app urls"
