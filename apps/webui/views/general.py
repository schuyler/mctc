#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from apps.mctc.models import MessageLog
from apps.webui.shortcuts import as_html, as_csv, as_pdf, paginate

from datetime import datetime

@login_required
def ajax_message_log(request):
    # always assume it's one page
    res = paginate(MessageLog.objects.order_by("-created_at"), 1)
    context = {
        "paginated_object_list": res,
        "paginate_url": "/message-log/"
    }
    return as_html(request, "messagelog-include.html", context)

@login_required
def message_log(request):
    # not sure if this is what matt wants yet, obviously doing this for lots
    # would be a pain, so we'll optimise this later when I know what is needed
    if request.GET.get("f") == "csv":
        res = MessageLog.objects.order_by("-created_at")
        return as_csv(request, res)
    elif request.GET.get("f") == "pdf":
        res = MessageLog.objects.order_by("-created_at")
        return as_pdf(request, res)
    else:
        res = paginate(MessageLog.objects.order_by("-created_at"), request.GET.get("p", 1))
        context = {
            "paginated_object_list": res,
            "paginate_url": "/message-log/"
        }
        return as_html(request, "messagelog.html", context)

@login_required
def dashboard(request):
    # i don't expect this to last, just a test and messing, ugh!
    today = datetime.today()
    messages = MessageLog.objects.filter(created_at__year=today.year).filter(created_at__month=today.month).filter(created_at__day=today.day)
    counts = [ [x, 0] for x in range(0, 24) ]
    for message in messages:
        # ugh!
        counts[message.created_at.hour][1] = counts[message.created_at.hour][1] + 1

    return as_html(request, "dashboard.html", {"counts":counts})

