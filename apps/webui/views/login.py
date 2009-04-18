from django.http import HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from apps.webui.forms.login import LoginForm
from apps.webui.shortcuts import as_html

def login(request):
    if request.method == "POST" and not request.user.is_authenticated():
        form = LoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(
                username=form.cleaned_data["username"], 
                password=form.cleaned_data["password"])
            if user:
                auth.login(request, user)
                return HttpResponseRedirect("/")
            else:
                return HttpResponseRedirect("/?msg=login_failed")
    else:
        form = LoginForm()
    return as_html(request, "login.html", { "form": form, })

    
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/")