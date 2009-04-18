from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from django.forms.util import ErrorList

from apps.webui.forms.base import BaseForm, BaseModelForm
from apps.mctc.models import Provider, Case

class MessageForm(BaseForm):
    message = forms.CharField(
        label = _("Message text"),
        required = True
    )
    
    groups = forms.MultipleChoiceField(
        label = _("Groups"),
        required = False,
        widget = forms.CheckboxSelectMultiple()
    )

    users = forms.MultipleChoiceField(
        label = _("Users"),
        required = False,        
        widget = forms.CheckboxSelectMultiple()
    )
    
    def clean(self):
        data = self.cleaned_data
        if not data.get("groups") and not data.get("users"):
            msg = _("You must specify either one or more groups or users.")
            self._errors["groups"] = ErrorList([msg,])
            
        return super(MessageForm, self).clean()
    
    def __init__(self, *args, **kw):
        super(MessageForm, self).__init__(*args, **kw)
        
        groups = [ (str(g.id), g.name) for g in Group.objects.all() ]
        users = [ (str(u.id), "%s %s" % (u.first_name, u.last_name)) for u in User.objects.all() ]
        self.fields["groups"].choices = groups
        self.fields["users"].choices = users

class CaseForm(BaseModelForm):
    class Meta:
        model = Case
        exclude = ('created_at', 'updated_at')