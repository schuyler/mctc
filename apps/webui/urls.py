#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import patterns

from apps.mctc.models import Case
from apps.webui.forms.general import CaseForm

urlpatterns = patterns('',
    (r'^$', "apps.webui.views.general.dashboard"),
    (r'^ajax/message-log/$', "apps.webui.views.general.ajax_message_log"),
    (r'^message-log/$', "apps.webui.views.general.message_log"),
    (r'^test/$', "apps.webui.views.details.detail"),
    (r'^search/$', "apps.webui.views.general.search_view"),
    (r'^district/$', "apps.webui.views.general.district_view"),    
    (r'^providers/$', "apps.webui.views.general.provider_list"),    
    (r'^provider/view/(?P<object_id>\d+)/$', "apps.webui.views.general.provider_view"),        
    
    (r'^case/(?P<object_id>\d+)/$', "apps.webui.views.general.case_view"),
    
    (r'^case/edit/(?P<object_id>\d+)/$', "django.views.generic.create_update.update_object", {
        "template_name": "caseedit.html",
        "form_class": CaseForm 
    }),
    
    # since we can't change settings, we have to do this as accounts/login
    (r'^accounts/login/$', "apps.webui.views.login.login"),    
    (r'^logout/$', "apps.webui.views.login.logout"),
    
    (r'^static/webui/(?P<path>.*)$', "django.views.static.serve",
        {"document_root": os.path.dirname(__file__) + "/static"})
)

