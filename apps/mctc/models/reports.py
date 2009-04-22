from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from apps.mctc.models.general import Case, Provider

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

class Observation(models.Model):
    uid = models.CharField(max_length=15)
    name = models.CharField(max_length=255)
    letter = models.CharField(max_length=2, unique=True)

    class Meta:
        app_label = "mctc"
        ordering = ("name",)

    def __unicode__(self):
        return self.name
        
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

    def get_dictionary(self):
        return {
            'result': self.result,
            'result_text': self.result and "Y" or "N",
            'bednet': self.bednet,
            'bednet_text': self.bednet and "Y" or "N",
            'observed': ", ".join([k.name for k in self.observed.all()]),            
        }
        
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

    def get_dictionary(self):
        return {
            'muac'      : "%d mm" % self.muac,
            'observed'  : ", ".join([k.name for k in self.observed.all()]),
            'diagnosis' : self.get_status_display(),
            'diagnosis_msg' : self.diagnosis_msg(),
        }
                               
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

class Lab(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    
    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "mctc"
        ordering = ("code",)        

class LabDiagnosis(models.Model):
    lab = models.ForeignKey(Lab)
    diagnosis = models.ForeignKey("ReportDiagnosis")
    amount = models.IntegerField(blank=True, null=True)
    result = models.BooleanField(blank=True)

    def __unicode__(self):
        return "%s, %s - %s" % (self.lab, self.diagnosis, self.amount)

    class Meta:
        app_label = "mctc"

class DiagnosisCategory(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "mctc"
        ordering = ("name",)
        
class Diagnosis(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    category = models.ForeignKey(DiagnosisCategory)
    mvp_code = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.mvp_code

    class Meta:
        app_label = "mctc"
        ordering = ("code",)
        
class ReportDiagnosis(Report, models.Model):
    case = models.ForeignKey(Case, db_index=True)
    provider = models.ForeignKey(Provider, db_index=True)
    diagnosis = models.ManyToManyField(Diagnosis)
    lab = models.ManyToManyField(Lab, through=LabDiagnosis)
    text = models.TextField()
    entered_at  = models.DateTimeField(db_index=True)
    
    def __unicode__(self):
        return self.case

    class Meta:
        verbose_name = "Diagnoses"
        app_label = "mctc"

    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportDiagnosis, self).save(*args)

    def get_dictionary(self):
        extra = []
        for ld in LabDiagnosis.objects.filter(diagnosis=self):
            if ld.amount:
                extra.append("%s %s" % (ld.lab.code, ld.amount))
            else:
                extra.append("%s%s" % (ld.lab.code, ld.result and "+" or "-"))
                
        return {
            "diagnosis": ", ".join([str(d) for d in self.diagnosis.all()]),
            "labs": ", ".join([str(d) for d in self.lab.all()]),
            "labs_text": ", ".join(extra)
        }
