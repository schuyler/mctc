from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from apps.mctc.models.general import Case, Provider, Observation

from datetime import datetime
import md5

class Report:
    def get_alert_recipients(self):
        """ Each report will send an alert, how it will choose when to send an alert
        is up to the model, however. """
        # this is the reporter, the provider or the CHW depending what you call it
        provider = self.provider
        facility = provider.clinic
        assert facility, "This provider does not have a clinic."

        recipients = []

        # find all the people assigned to alerts from this facility
        for user in facility.following_clinics.all():
            # only send if they want
            if user.alerts:
                if user not in recipients:
                    recipients.append(user)
        
        
        # find all the users monitoring this user
        for user in provider.following_users.all():
            if user.alerts:
                if user not in recipients:
                    recipients.append(user)

        return recipients
        
class ReportMalaria(Report, models.Model):
    class Meta:
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)
        app_label = "mctc"
    
    case = models.ForeignKey(Case, db_index=True)
    provider = models.ForeignKey(Provider, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    diagnosis = models.ManyToManyField("Diagnosis")
    bednet = models.BooleanField(db_index=True)
    result = models.BooleanField(db_index=True) 
    observed = models.ManyToManyField(Observation)       

    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportMalaria, self).save(*args)
        
class ReportMalnutrition(Report, models.Model):
    class Meta:
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)

    MODERATE_STATUS         = 1
    SEVERE_STATUS           = 2
    SEVERE_COMP_STATUS      = 3
    HEALTHY_STATUS = 4
    STATUS_CHOICES = (
        (MODERATE_STATUS,       _('MAM')),
        (SEVERE_STATUS,         _('SAM')),
        (SEVERE_COMP_STATUS,    _('SAM+')),
        (HEALTHY_STATUS, _("Healthy")),
    )

    case        = models.ForeignKey(Case, db_index=True)
    provider    = models.ForeignKey(Provider, db_index=True)
    entered_at  = models.DateTimeField(db_index=True)
    muac        = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height      = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight      = models.FloatField(_("Weight (kg)"), null=True, blank=True)
    observed    = models.ManyToManyField(Observation)
    status      = models.IntegerField(choices=STATUS_CHOICES, db_index=True, blank=True, null=True)
                               
    def __unicode__ (self):
        return "#%d" % self.id
    
    def diagnose (self):
        complications = [c for c in self.observed.all() if c.uid != "edema"]
        edema = "edema" in [ c.uid for c in self.observed.all() ]
        self.status = ReportMalnutrition.HEALTHY_STATUS
        if edema or self.muac < 110:
            if complications:
                self.status = ReportMalnutrition.SEVERE_COMP_STATUS
            else:
                self.status =  ReportMalnutrition.SEVERE_STATUS
        elif self.muac < 125:
            self.status =  ReportMalnutrition.MODERATE_STATUS

    def diagnosis_msg(self):
        if self.status == 1:
            msg = "MAM Child requires supplemental feeding."
        elif self.status == 2:
            msg = "SAM Patient requires OTP care"
        elif self.status == 3:
            msg = "SAM+ Patient requires IMMEDIATE inpatient care"
        else:
            msg = "Child is not malnourished"

        return msg

    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportMalnutrition, self).save(*args)

    class Meta:
        app_label = "mctc"


class DiagnosisCategory(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "mctc"

class Diagnosis(models.Model):
    name = models.CharField(max_length=255)
    short_code = models.CharField(max_length=1)
    category = models.ForeignKey(DiagnosisCategory)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "mctc"
        
class ReportDiagnosis(Report, models.Model):
    name = models.CharField(max_length=255)
    diagnosis = models.CharField(max_length=1)

    def __unicode__(self):
        return self.numeric_code

    class Meta:
        verbose_name = "Diagnoses"
        app_label = "mctc"

# this needs to die
class ReportCache(models.Model):
    case = models.ForeignKey(Case)
    date = models.DateField(db_index=True)
    muac = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight = models.FloatField(_("Weight (kg)"), null=True, blank=True)

    class Meta:
        app_label = "mctc"
