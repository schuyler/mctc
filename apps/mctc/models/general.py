from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from datetime import datetime
import md5

class Zone(models.Model):
    def __unicode__ (self): 
        return self.name

    class Meta:
        app_label = "mctc"
    
    CLUSTER_ZONE = 1
    VILLAGE_ZONE = 2
    SUBVILLAGE_ZONE = 3
    ZONE_TYPES = (
        (CLUSTER_ZONE, _('Cluster')),
        (VILLAGE_ZONE, _('Village')),
        (SUBVILLAGE_ZONE, _('Sub village'))
    )
    
    number = models.PositiveIntegerField(unique=True,db_index=True)
    name = models.CharField(max_length=255)
    head = models.ForeignKey("self", null=True,blank=True)
    category = models.IntegerField(choices=ZONE_TYPES, default=VILLAGE_ZONE)
    lon = models.FloatField(null=True,blank=True)
    lat = models.FloatField(null=True,blank=True)

class Facility(models.Model):
    def __unicode__ (self): 
        return self.name
        
    class Meta:
        verbose_name_plural = "Facilities"
        app_label = "mctc"

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
    def __unicode__ (self): 
        return self.mobile

    class Meta:
        app_label = "mctc"
    
    CHW_ROLE    = 1
    NURSE_ROLE  = 2
    DOCTOR_ROLE = 3
    SENIOR_CHW_ROLE = 4
    CLINICAL_OFFICER_ROLE = 5
    NUTRITIONIST_ROLE = 6
    HEALTH_FAC_ROLE = 7
    HEALTH_COR_ROLE = 8
    
    ROLE_CHOICES = (
        (CHW_ROLE,    _('CHW')),
        (NURSE_ROLE,  _('Nurse')),
        (DOCTOR_ROLE, _('Doctor')),
        (SENIOR_CHW_ROLE, _("Senior CHW")),
        (CLINICAL_OFFICER_ROLE, _("Clinical Officer")),
        (NUTRITIONIST_ROLE, _("Nutritionist")),
        (HEALTH_FAC_ROLE, _("Health Facilitator")),
        (HEALTH_COR_ROLE, _("Health Co-ordinator")),        
    )
    
    user    = models.OneToOneField(User)
    mobile  = models.CharField(max_length=16, null=True, db_index=True)
    role    = models.IntegerField(choices=ROLE_CHOICES, default=CHW_ROLE)
    active  = models.BooleanField(default=True)
    alerts  = models.BooleanField(default=False, db_index=True)
    clinic  = models.ForeignKey(Facility, null=True, db_index=True)
    manager = models.ForeignKey("Provider", blank=True, null=True)
    following_users = models.ManyToManyField("Provider", related_name="following_users", blank=True, null=True)
    following_clinics = models.ManyToManyField(Facility, related_name="following_clinics", blank=True, null=True)

    def get_absolute_url(self):
        return "/provider/view/%s/" % self.id

    @classmethod
    def by_mobile (cls, mobile):
        try:
            return cls.objects.get(mobile=mobile, active=True)
        except models.ObjectDoesNotExist:
            return None

class Case(models.Model):    
    class Meta:
        app_label = "mctc"
    
    GENDER_CHOICES = (
        ('M', _('Male')), 
        ('F', _('Female')), 
    )
    
    ref_id      = models.IntegerField(_('Case ID #'), null=True, db_index=True)
    first_name  = models.CharField(max_length=255, db_index=True)
    last_name   = models.CharField(max_length=255, db_index=True)
    gender      = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob         = models.DateField(_('Date of Birth'))
    guardian    = models.CharField(max_length=255, null=True, blank=True)
    mobile      = models.CharField(max_length=16, null=True, blank=True)
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
    
    def years_months(self):
        now = datetime.now().date()
        return (now.year - self.dob.year, now.month - self.dob.month)
    
    def age(self):
        delta = datetime.now().date() - self.dob
        years = delta.days / 365.25
        if years > 3:
            return str(int(years))
        else:
            # FIXME: i18n
            return str(int(delta.days/30.4375))+"m"

class Observation(models.Model):
    uid = models.CharField(max_length=15)
    name = models.CharField(max_length=255)
    letter = models.CharField(max_length=2, unique=True)

    class Meta:
        app_label = "mctc"

    def __unicode__(self):
        return self.name

class CaseNote(models.Model):
    case        = models.ForeignKey(Case, related_name="notes", db_index=True)
    created_by  = models.ForeignKey(User, db_index=True)
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)
    text        = models.TextField()

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        super(CaseNote, self).save(*args)

    class Meta:
        app_label = "mctc"

class MessageLog(models.Model):
    mobile      = models.CharField(max_length=255, db_index=True)
    sent_by     = models.ForeignKey(User, null=True)
    text        = models.CharField(max_length=255)
    was_handled = models.BooleanField(default=False, db_index=True)
    created_at  = models.DateTimeField(db_index=True)

    class Meta:
        app_label = "mctc"

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        super(MessageLog, self).save(*args)