from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^', include('emailconfirmation.urls')),
    url(r'^login/$', 'django.contrib.auth.views.login', name='auth_login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='auth_logout'),
)
