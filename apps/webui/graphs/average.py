from django.db.models import Count, ObjectDoesNotExist, Q, Avg

import time
from datetime import datetime, timedelta

from apps.mctc.models.reports import ReportCache, ReportMalnutrition, Case
from apps.webui.graphs.flot import FlotGraph


def create_average_for_case(case, field, length):
    now = datetime.now()
    start = now - timedelta(days=length)

    last_cache = ReportCache.objects.filter(case=case).order_by("-date")
    if not last_cache:
        last_cache_date = start
    else:
        last_cache_date = last_cache[0].date
    
    if last_cache_date < now:
        for fld in ("muac", "weight", "height"):
            reports = {}        
            last = None            
            for report in ReportCache.objects.filter(case=case):
                reports[report.entered_at.date()] = getattr(report, fld)
    
            # find the first
            first = ReportMalnutrition.objects.filter(case=case).filter(entered_at__lte=last_cache_date).order_by("-entered_at")
            if first:
                last = getattr(report, fld)
        
            for x in range(0, (now - last_cache_date).days + 1):
                date = (start + timedelta(days=x)).date()
                if reports.has_key(date):
                    last = reports[date]
                if last:
                    obj = ReportCache.objects.get_or_create(case=case, date=date)[0]
                    setattr(obj, fld, last)
                    obj.save()
                x += 1

    res = ReportCache.objects.filter(case=case).filter(date__gte=start)
    rows = [ [time.mktime(r.date.timetuple()) * 1000, getattr(r, field) ] for r in res if getattr(r, field) ]
    return rows

def create_average_for_qs(q, field, length):
    # ensure cache is up to date
    for case in Case.objects.filter(q):
        create_average_for_case(case, field, length)

    
    now = datetime.now().date()
    start = now - timedelta(days=length)

    rows = []

    for x in range(0, (now - start).days + 1):
        res = ReportCache.objects.filter(q).filter(date=start + timedelta(days=x)).values("date").annotate(Avg(field))
        if res:
            rows.append([
                time.mktime(res[0]["date"].timetuple()) * 1000,
                res[0][field + "__avg"]
                ])
        x += 1

    return rows

def create_graph(data, name):
    graph = FlotGraph()
    graph.set_data([{"data":data, "label":name},])
    graph.set_zoomable(1)
    graph.set_xaxis_mode("time")
    graph.set_time_format("%m/%d/%y")
    graph.set_title(name)
    graph.generate_javascript()
    
    return graph