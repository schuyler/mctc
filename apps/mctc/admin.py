from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from models.general import Zone, Facility, Case, Provider, User 
from models.logs import MessageLog, EventLog
from models.reports import ReportMalnutrition, Observation
from django.utils.translation import ugettext_lazy as _

class ProviderInline (admin.TabularInline):
    """Allows editing Users in admin interface style"""
    model   = Provider
    fk_name = 'user'
    max_num = 1

class ProviderAdmin (UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser')}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    inlines     = (ProviderInline,)
    #list_filter = ['is_active']

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, ProviderAdmin)

class CaseAdmin(admin.ModelAdmin):
    list_display = ("ref_id", "first_name", "last_name", "gender", "dob", "zone")

admin.site.register(Case, CaseAdmin)
admin.site.register(Provider)
admin.site.register(Zone)
admin.site.register(Facility)

class ReportMalnutritionAdmin(admin.ModelAdmin):
    list_display = ("case", "muac", "height", "weight", "entered_at")

admin.site.register(ReportMalnutrition, ReportMalnutritionAdmin)

class MessageLogAdmin(admin.ModelAdmin):
    list_display = ("mobile", "sent_by", "text", "created_at", "was_handled")
    list_filter = ("was_handled",)
    
admin.site.register(MessageLog, MessageLogAdmin)
admin.site.register(EventLog)
