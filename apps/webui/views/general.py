#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.db.models import Count, ObjectDoesNotExist, Q, Avg
from django.db import connection

from apps.mctc.models import MessageLog, Case, Zone, Provider, Report, ReportCache
from apps.mctc.app import message_users

from apps.webui.shortcuts import as_html, as_csv, as_pdf, paginate, login_required
from apps.webui.forms.general import MessageForm

from apps.webui.graphs.flot import FlotGraph
from apps.webui.graphs.average import create_average_for_qs, create_graph

from datetime import datetime, timedelta
import time

@login_required
def ajax_message_log(request):
    # always assume it's one page
    res = paginate(MessageLog.objects.order_by("-created_at"), 1)
    context = {
        "paginated_object_list": res,
        "paginate_url": "/message-log/"
    }
    return as_html(request, "includes/messagelog.html", context)

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
def active_cases(request):
    qs = Case.objects.order_by("-updated_at");
    if request.GET.get("f") == "csv":
        return as_csv(request, qs)
    elif request.GET.get("f") == "pdf":
        return as_pdf(request, qs)

    res = paginate(qs, 1, 50)
    context = {
        "paginated_object_list": res,
        "paginate_url": "/message-log/"
    }
    if request.is_ajax:
        return as_html(request, "includes/activecases.html", context)
    else:
        return as_html(request, "activecases.html", context)

    
@login_required
def dashboard(request):
    # i don't expect this to last, just a test and messing, ugh!
    res = paginate(Case.filter_ill().order_by("-updated_at"), 1, 50)
    # get totals, yay for aggregation and turn it into a dict for easy use in templates
    totals = Case.objects.values("status").annotate(Count("status"))
    totals = dict([ [t["status"], t["status__count"] ] for t in totals ])
 
    case = Case.objects.get(id=1)
    averages = { 
        "muac": create_graph(data=create_average_for_qs(Q(), "muac", 30), name="muac"),
#        "weight": create_graph(data=create_average_for_qs(Q(), "weight", 90), name="weight"),
#        "height": create_graph(data=create_average_for_qs(Q(), "height", 90), name="height"),
    }
    
    has_provider = True
    try:
        mobile = request.user.provider.mobile
        if request.method == "POST":
            messageform = MessageForm(request.POST)
            if messageform.is_valid():
                message_users(mobile, **messageform.cleaned_data)
                return HttpResponseRedirect("/?msg=message_sent")
        else:
            messageform = MessageForm()
    except ObjectDoesNotExist:
        has_provider = False
        messageform = None
        
    context = {
        "case_object_list": res,
        "paginate_url": "#",
        "case_totals": totals,
        "message_form": messageform,
        "has_provider": has_provider,
        "averages": averages,
    }
    return as_html(request, "dashboard.html", context)

@login_required
def search_view(request):
    term = request.GET.get("q")
    # need to make this case insensitive
    query = Q(id__contains=term) | Q(first_name__contains=term) | Q(last_name__contains=term)
    queryset = Case.objects.filter(query)
    res = paginate(queryset, 1)
    context = {
        "case_object_list": res,
    }
    return as_html(request, "searchview.html", context)
    
@login_required
def case_view(request, object_id):
    case = get_object_or_404(Case, id=object_id)
    res = paginate(case.report_set.all(), 1)
    context = {
        "object": case,
        "report_object_list": res
    }
    return as_html(request, "caseview.html", context)

@login_required
def district_view(request):
    district = request.GET.get("d")
    context = {
        "districts": Zone.objects.all(),
    }
    if district:
        zone = get_object_or_404(Zone, id=district)
        res = paginate(Case.filter_ill().filter(zone=zone), 1)
        context["case_object_list"] = res

    return as_html(request, "districtview.html", context)

@login_required
def provider_list(request):
    res = paginate(Provider.objects.all(), 1)
    context = {
        "provider_object_list": res,
    }
    return as_html(request, "providerlist.html", context)

@login_required
def provider_view(request, object_id):
    provider = get_object_or_404(Provider, id=object_id)
    context = {
        "object": provider,
        "case_object_list": paginate(Case.filter_ill().filter(provider=provider), 1),
        "message_object_list": paginate(MessageLog.objects.filter(sent_by=provider.user).order_by("-created_at"), 1)
        
    }
    return as_html(request, "providerview.html", context)
