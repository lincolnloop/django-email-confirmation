from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^confirm/(\w+)/$', 'emailconfirmation.views.confirm_email',
        name="emailconfirmation_confirm"),
)
