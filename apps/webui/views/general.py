#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.db.models import Count, ObjectDoesNotExist, Q, Avg
from django.db import connection

from apps.mctc.models.logs import MessageLog, EventLog
from apps.mctc.models.general import Case, Zone, Provider
from apps.mctc.models.reports import ReportMalnutrition, ReportMalaria, ReportDiagnosis

from apps.webui.shortcuts import as_html, login_required
from apps.webui.forms.general import MessageForm

from datetime import datetime, timedelta
import time

from apps.reusable_tables.table import get


@login_required
def dashboard(request):
    nonhtml, tables = get(request, [
        ["case", Q()],
        ["event", Q()],
    ])
    if nonhtml:
        return nonhtml

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
        "case_table": tables[0],
        "event_table": tables[1],
        "message_form": messageform,
        "has_provider": has_provider
    }
    return as_html(request, "dashboard.html", context)

@login_required
def search_view(request):
    term = request.GET.get("q")
    query = Q(id__icontains=term) | \
            Q(first_name__icontains=term) | \
            Q(last_name__icontains=term)

    cases = Case.objects.filter(query).order_by("-updated_at")
    format, case_table = get("case_default")(request, "cases", cases)
    if format != "html": return case_table

    return as_html(request, "searchview.html", { "case_table": case_table, })

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
