from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from fields import SeparatedValuesField

from datetime import datetime
import md5

class Zone(models.Model):
    def __unicode__ (self): return self.name
    number  = models.PositiveIntegerField(unique=True,db_index=True)
    name    = models.CharField(max_length=255)
    lon     = models.FloatField(null=True,blank=True)
    lat     = models.FloatField(null=True,blank=True)

class Facility(models.Model):
    def __unicode__ (self): return self.name
    class Meta:
        verbose_name_plural = "Facilities"

    CLINIC_ROLE  = 1
    DISTRIB_ROLE = 2
    ROLE_CHOICES = (
        (CLINIC_ROLE,  _('Clinic')),
        (DISTRIB_ROLE, _('Distribution Point')),
    )
    name        = models.CharField(max_length=255)
    role        = models.IntegerField(choices=ROLE_CHOICES, default=CLINIC_ROLE)
    zone        = models.ForeignKey(Zone,db_index=True)
    codename    = models.CharField(max_length=255,unique=True,db_index=True)
    lon         = models.FloatField(null=True,blank=True)
    lat         = models.FloatField(null=True,blank=True)

class Provider(models.Model):
    def __unicode__ (self): return self.mobile
    CHW_ROLE    = 1
    NURSE_ROLE  = 2
    DOCTOR_ROLE = 3
    ROLE_CHOICES = (
        (CHW_ROLE,    _('CHW')),
        (NURSE_ROLE,  _('Nurse')),
        (DOCTOR_ROLE, _('Doctor'))
    )
    user    = models.OneToOneField(User)
    mobile  = models.CharField(max_length=16, null=True, db_index=True)
    role    = models.IntegerField(choices=ROLE_CHOICES, default=CHW_ROLE)
    active  = models.BooleanField(default=True)
    alerts  = models.BooleanField(default=False, db_index=True)
    clinic  = models.ForeignKey(Facility, null=True, db_index=True)
    manager = models.ForeignKey("Provider", blank=True, null=True)

    def get_absolute_url(self):
        return "/provider/view/%s/" % self.id

    @classmethod
    def by_mobile (cls, mobile):
        try:
            return cls.objects.get(mobile=mobile, active=True)
        except models.ObjectDoesNotExist:
            return None

class Case(models.Model):
    GENDER_CHOICES = (
        ('M', _('Male')), 
        ('F', _('Female')), 
    )
    UNKNOWN_STATUS          = 1
    HEALTHY_STATUS          = 2
    ILL_STATUS              = 3
    MODERATE_STATUS         = 4
    SEVERE_STATUS           = 5
    SEVERE_COMP_STATUS      = 6
    CURED_STATUS            = 7
    DECEASED_STATUS         = 8
    DEFAULTED_STATUS        = 9
    NOT_RECOVERED_STATUS    = 10
    TRANSFERRED_STATUS      = 11
    STATUS_CHOICES = (
        (UNKNOWN_STATUS,        _('Unknown')),
        (HEALTHY_STATUS,        _('Healthy')),
        (ILL_STATUS,            _('Ill')),
        (MODERATE_STATUS,       _('MAM')),
        (SEVERE_STATUS,         _('SAM')),
        (SEVERE_COMP_STATUS,    _('SAM+')),
        (CURED_STATUS,          _('Cured')),
        (DECEASED_STATUS,       _('Deceased')),
        (DEFAULTED_STATUS,      _('Defaulted')),
        (NOT_RECOVERED_STATUS,  _('Not Recovered')),
        (TRANSFERRED_STATUS,    _('Transferred')),
    )
    ref_id      = models.IntegerField(_('Case ID #'), null=True, db_index=True)
    first_name  = models.CharField(max_length=255, db_index=True)
    last_name   = models.CharField(max_length=255, db_index=True)
    gender      = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob         = models.DateField(_('Date of Birth'))
    guardian    = models.CharField(max_length=255, null=True, blank=True)
    mobile      = models.CharField(max_length=16, null=True, blank=True)
    status      = models.IntegerField(choices=STATUS_CHOICES,
                               default=HEALTHY_STATUS, db_index=True)
    provider    = models.ForeignKey(Provider, db_index=True)
    zone        = models.ForeignKey(Zone, null=True, db_index=True)
    village     = models.CharField(max_length=255, null=True, blank=True)
    district    = models.CharField(max_length=255, null=True, blank=True)
    created_at  = models.DateTimeField()
    updated_at  = models.DateTimeField()

    def get_absolute_url(self):
        return "/case/%s/" % self.id

    def __unicode__ (self):
        return "#%d" % self.ref_id

    def _luhn (self, x):
        parity = True
        sum = 0
        for c in reversed(str(x)):
            n = int(c)
            if parity:
                n *= 2
                if n > 9: n -= 9
            sum += n
        return x * 10 + 10 - sum % 10

    def save (self, *args):
        if not self.id:
            self.created_at = self.updated_at = datetime.now()
        else:
            self.updated_at = datetime.now()
        super(Case, self).save(*args)
        if not self.ref_id:
            self.ref_id = self._luhn(self.id)
            super(Case, self).save(*args)
    
    def age (self):
        delta = datetime.now().date() - self.dob
        years = delta.days / 365.25
        if years > 3:
            return str(int(years))
        else:
            # FIXME: i18n
            return str(int(delta.days/30.4375))+"m"

    @classmethod
    def filter_ill(cls):
        # as per requirements from Matt, to show MAM, SAM and SAM+
        return cls.objects.filter(status__in=[cls.MODERATE_STATUS, cls.SEVERE_STATUS, cls.SEVERE_COMP_STATUS])

    @classmethod
    def filter_active(cls):
        return cls.objects.filter(status__le=cls.CURED_STATUS)

class Report(models.Model):
    class Meta:
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)

    EDEMA_OBSERVED         = 1
    APPETITE_LOSS_OBSERVED = 2
    DIARRHEA_OBSERVED      = 3
    VOMITING_OBSERVED      = 4
    CHRONIC_COUGH_OBSERVED = 5
    HIGH_FEVER_OBSERVED    = 6
    UNRESPONSIVE_OBSERVED  = 7
    OBSERVED_CHOICES = (
        (EDEMA_OBSERVED,         _("Edema")),
        (APPETITE_LOSS_OBSERVED, _("Appetite Loss")),
        (DIARRHEA_OBSERVED,      _("Diarrhea")),
        (VOMITING_OBSERVED,      _("Vomiting")),
        (CHRONIC_COUGH_OBSERVED, _("Chronic Cough")),
        (HIGH_FEVER_OBSERVED,    _("High Fever")),
        (UNRESPONSIVE_OBSERVED,  _("Unresponsive")),
    )
    case        = models.ForeignKey(Case, db_index=True)
    provider    = models.ForeignKey(Provider, db_index=True)
    entered_at  = models.DateTimeField(db_index=True)
    muac        = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height      = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight      = models.FloatField(_("Weight (kg)"), null=True, blank=True)
    observed    = SeparatedValuesField(_("Observations"),
                    choices=OBSERVED_CHOICES, max_length=255,
                    null=True, blank=True)

    def get_observed_display(self):
        # can we move this to the field?
        # not sure what i'm going to get back, lets get some data
        pass
        
    def __unicode__ (self):
        return "#%d" % self.id
    
    def diagnosis (self):
        complications = [c for c in self.observed if c != self.EDEMA_OBSERVED]
        edema = self.EDEMA_OBSERVED in self.observed
        if edema or self.muac < 110:
            if complications:
                return Case.SEVERE_COMP_STATUS
            else:
                return Case.SEVERE_STATUS
        elif self.muac < 125:
            return Case.MODERATE_STATUS
        elif complications:
            return Case.ILL_STATUS
        else: 
            return Case.HEALTHY_STATUS

    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(Report, self).save(*args)


class CaseNote(models.Model):
    case        = models.ForeignKey(Case, related_name="notes", db_index=True)
    created_by  = models.ForeignKey(User, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    text        = models.TextField()

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        super(CaseNote, self).save(*args)

class MessageLog(models.Model):
    mobile      = models.CharField(max_length=255, db_index=True)
    sent_by     = models.ForeignKey(User, null=True)
    text        = models.CharField(max_length=255)
    was_handled = models.BooleanField(default=False, db_index=True)
    created_at  = models.DateTimeField(db_index=True)

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        super(MessageLog, self).save(*args)

class ReportCache(models.Model):
    case = models.ForeignKey(Case)
    date = models.DateField(db_index=True)
    muac = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight = models.FloatField(_("Weight (kg)"), null=True, blank=True)
