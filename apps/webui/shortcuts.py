from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response

def as_html(request, template, context):
    return render_to_response(template, 
        context,
        context_instance=RequestContext(request)
        )
    
def login_required(fn):
    """ We need to limit the front end to authenticated staff """
    def new(*args, **kw):
        request = args[0]
        if request.user.is_authenticated:
            if request.user.is_staff and request.user.is_active:
                return fn(*args, **kw)
        
        return HttpResponseRedirect("/accounts/login/")
    return new
    