# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
#from muac_weekly.muac.models import Patient, Patient_Muac
from django.http import HttpResponse
from apps.webui.grapher import FlotGraph
array_time = [[1233468000000, 1],[1233469000000, 1], [1233471000000, 1.8]]
time_data = [{'data': array_time, 'label': "Temperature"}]

d1 = [[1, 11],[2, 12],[3, 13]]
d2 = [[1, 14], [2,17], [3,18], [4,19]]
d3 = [[11, 1],[12, 2],[13, 3]]
d4 = [[1, 4], [2,7], [3,8], [4,9]]
array_of_series = [{'data': d1, 'label': "United States", 'lines': {'fill': ".5", 'lineWidth': "2"}, }, {'data': d2, 'label': "Russia", 'bars': {'barWidth': ".2", 'align': "center"}}, {'data': d3, 'label': "United Kingdom", 'points':{}}, {'data': d4,}]

array_of_markings = [{'xaxis': {'from': "0", 'to': "6"}, 'yaxis': {'from': "5", 'to': "6"}, 'color': "#bb0000", 'label': "danger zone"}, {'xaxis': {'from': "9", 'to': "11"}, 'color': "#bbaa00", 'label': "Ugly Color"}]
sample_array = [{'data': d1}, {'data': d2}, {'data': d3}]
#datasets = [[[1, 11],[2, 12],[3, 13]], [[1, 14], [2,17], [3,18], [4,19]], [[11, 1],[12, 2],[13, 3]]]
#toggle_labels = ["United States", "Russia", "United Kingdom"]

g_time = FlotGraph()
g_time.set_data(time_data)
g_time.set_xaxis_mode("time")
g_time.set_time_format("%h:%M %d/%m")
g_time.set_zoomable(0)
g_time.set_key_position(0)
g_time.set_display_title("Temperature: Morning of January 2")
g_time.generate_javascript()
g = FlotGraph()
g.set_markings(array_of_markings)
g.set_title("amazing flot graph")
g.set_display_title("Amazing Flot Graph")
g.set_zoomable(1)
g.set_key_position(0)
g.set_xaxis_max("15")
g.set_yaxis_max("19")

g.set_toggle_data(array_of_series)
#g.set_xaxis_mode("time")

#g.set_xaxis_options("mode: \"time\", \n timeformat: \"%m/%d\",") 
g.generate_javascript()

def detail(request):
	return render_to_response('detail.html', { 'graph': g, 'time_graph': g_time})
