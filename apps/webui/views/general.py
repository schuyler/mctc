#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.db.models import ObjectDoesNotExist, Q
from django.contrib.auth.models import User, Group
from django.db import connection

from apps.mctc.models.logs import MessageLog, EventLog
from apps.mctc.models.general import Case, Zone, Provider
from apps.mctc.models.reports import ReportMalnutrition, ReportMalaria, ReportDiagnosis

from apps.webui.shortcuts import as_html, login_required
from apps.webui.forms.general import MessageForm

from datetime import datetime, timedelta
import time

from urllib import quote, urlopen
from apps.reusable_tables.table import get

# not quite sure how to figure this out programatically
domain = "localhost"
port = "8080"

def message_users(mobile, message=None, groups=None, users=None):
    # problems that might still exist here
    # timeouts in the browser because we have to post all the messages
    # timeouts in the url request filtering up to the above
    recipients = []
    # get all the users
    provider_objects = [ Provider.objects.get(id=user) for user in users ]
    for provider in provider_objects:
        try:
            if provider not in recipients:
                recipients.append(provider)
        except models.ObjectDoesNotExist:
            pass
     # get all the users for the groups
    group_objects = [ Group.objects.get(id=group) for group in groups ]
    for group in group_objects:
        for user in group.user_set.all():
            try:
                if user.provider not in recipients:
                    recipients.append(user.provider)
            except models.ObjectDoesNotExist:
                pass
    
    passed = []
    failed = []
    for recipient in recipients:
        msg = quote("@%s %s" % (recipient.id, message))
        cmd = "http://%s:%s/%s/%s" % (domain, port, mobile, msg)
        try:
            urlopen(cmd).read()
            passed.append(recipient)
        except IOError:
            # if the mobile number is badly formed and the number regex fails
            # this is the error that is raised
            failed.append(recipient)
    
    results_text = ""
    if not passed and not failed:
        results_text = "No recipients were sent that message."
    elif not failed and passed:
        results_text = "The message was sent to %s recipients" % (len(passed))
    elif failed and passed:
        results_text = "The message was sent to %s recipients, but failed for the following: %s" % (len(passed), ", ".join([ str(f) for f in failed]))
    elif not passed and failed:
        results_text = "No-one was sent that message. Failed for the following: %s" % ", ".join([ str(f) for f in failed])
    return results_text

def get_graph(length=100, filter=Q()):
    end = datetime.now().date()
    start = end - timedelta(days=100)
    results = ReportMalnutrition.objects\
        .filter(Q()).exclude(muac=None)\
        .filter(entered_at__gt=start)\
        .filter(entered_at__lte=end)\
        .order_by("-entered_at")\
        .values_list("muac", "entered_at")
    results = [ [ time.mktime(r[1].timetuple()) * 1000,  r[0] ] for r in results ]
    results = { "start":'"%s"' % start.strftime("%Y/%m/%d"), "end":'"%s"' % end.strftime("%Y/%m/%d"), "results":results }
    return results
    
def get_summary():
    # i can't figure out a good way to do this, i'm sure it will all change, so
    # let's do slow and dirty right now
    seen = []
    status = {
        ReportMalnutrition.MODERATE_STATUS: 0,
        ReportMalnutrition.SEVERE_STATUS: 0,
        ReportMalnutrition.SEVERE_COMP_STATUS: 0,
        ReportMalnutrition.HEALTHY_STATUS: 0,
    }
    
    # please fix me
    for rep in ReportMalnutrition.objects.order_by("-entered_at"):
        if rep.status:
            if rep.id not in seen:
                seen.append(rep.id)
            status[rep.status] += 1

    data = {
        "mam": status[ReportMalnutrition.MODERATE_STATUS],
        "sam": status[ReportMalnutrition.SEVERE_STATUS],
        "samplus": status[ReportMalnutrition.SEVERE_COMP_STATUS],
    }
    return data

@login_required
def dashboard(request):
    nonhtml, tables = get(request, [
        ["case", Q()],
        ["event", Q()],
        ["message", Q()],
    ])
    if nonhtml:
        return nonhtml

    has_provider = True
    context = {
        "case_table": tables[0],
        "event_table": tables[1],
        "message_table": tables[2]
    }    

    try:
        mobile = request.user.provider.mobile
        if request.method == "POST":
            messageform = MessageForm(request.POST)
            if messageform.is_valid():
                result = message_users(mobile, **messageform.cleaned_data)
                context["msg"] = result
        else:
            messageform = MessageForm()
    except ObjectDoesNotExist:
        has_provider = False
        messageform = None

    context.update({
            "message_form": messageform,
            "has_provider": has_provider,
            "summary": get_summary(),
            "graph": get_graph()
        })

    return as_html(request, "dashboard.html", context)

@login_required
def search_view(request):
    term = request.GET.get("q")
    query = Q(id__icontains=term) | \
            Q(first_name__icontains=term) | \
            Q(last_name__icontains=term)

    nonhtml, tables = get(request, [ ["case", query], ])
    if nonhtml: 
        return nonhtml

    return as_html(request, "searchview.html", { "search": tables[0], })

@login_required
def case_view(request, object_id):
    case = get_object_or_404(Case, id=object_id)
    nonhtml, tables = get(request, [
        ["malnutrition", Q(case=case)],
        ["diagnosis", Q(case=case)],
        ["malaria", Q(case=case)],
        ["event", Q(content_type="case", object_id=object_id)],
        ])

    if nonhtml:
        return nonhtml

    context = {
        "object": case,
        "malnutrition": tables[0],
        "diagnosis": tables[1],
        "malaria": tables[2],
        "event": tables[3],
    }
    return as_html(request, "caseview.html", context)

@login_required
def district_view(request):
    district = request.GET.get("d")
    context = {
        "districts": Zone.objects.all(),
    }
    if district:
        nonhtml, tables = get(request, (["case", Q(zone=district)],))
        if nonhtml:
            return nonhtml
        context["cases"] = tables[0]

    return as_html(request, "districtview.html", context)

@login_required
def provider_list(request):
    nonhtml, tables = get(request, (["provider", Q()],))
    if nonhtml:
        return nonhtml
    context = {
        "provider": tables[0],
    }
    return as_html(request, "providerlist.html", context)

@login_required
def provider_view(request, object_id):
    provider = get_object_or_404(Provider, id=object_id)
    nonhtml, tables = get(request, (
        ["case", Q(provider=provider)],
        ["message", Q(sent_by=provider.user)],
        ["event", Q(content_type="provider", object_id=provider.pk)]
        ))
    if nonhtml:
        return nonhtml
    context = {
        "object": provider,
        "cases": tables[0],
        "messages": tables[1],
        "event": tables[2]
    }
    return as_html(request, "providerview.html", context)
