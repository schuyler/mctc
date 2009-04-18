#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import patterns
import apps.webui.views as views

urlpatterns = patterns('',
    (r'^$', "apps.webui.views.general.dashboard"),
    (r'^ajax/message-log/$', "apps.webui.views.general.ajax_message_log"),
    (r'^message-log/$', "apps.webui.views.general.message_log"),
    
    # since we can't change settings, we have to do this as accounts/login
    (r'^accounts/login/$', "apps.webui.views.login.login"),    
    (r'^logout/$', "apps.webui.views.login.logout"),
    
    (r'^static/webui/(?P<path>.*)$', "django.views.static.serve",
        {"document_root": os.path.dirname(__file__) + "/static"})
)

