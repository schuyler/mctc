from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from models import *

def _(arg): return arg

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

admin.site.register(Zone)
admin.site.register(Facility)
admin.site.register(Case)
admin.site.register(MessageLog)

