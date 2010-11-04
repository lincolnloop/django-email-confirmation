from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^confirm/(\w+)/$', 'emailconfirmation.views.confirm',
        name="emailconfirmation_confirm"),
)
