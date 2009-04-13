from django.db.models import *
from django.contrib.auth.models import User
from fields import SeparatedValuesField
import md5

def _(arg): return arg

class Zone (Model):
    def __unicode__ (self): return self.name
    number  = PositiveIntegerField(unique=True)
    name    = CharField(max_length=255)
    lon     = FloatField(null=True,blank=True)
    lat     = FloatField(null=True,blank=True)

class Facility (Model):
    def __unicode__ (self): return self.name
    class Meta:
        verbose_name_plural = "Facilities"

    CLINIC_ROLE  = 1
    DISTRIB_ROLE = 2
    ROLE_CHOICES = (
        (CLINIC_ROLE,  _('Clinic')),
        (DISTRIB_ROLE, _('Distribution Point')),
    )
    name        = CharField(max_length=255)
    role        = IntegerField(choices=ROLE_CHOICES, default=CLINIC_ROLE)
    zone        = ForeignKey(Zone)
    codename    = CharField(max_length=255,unique=True)
    lon         = FloatField(null=True,blank=True)
    lat         = FloatField(null=True,blank=True)

class Provider (Model):
    def __unicode__ (self): return self.mobile
    CHW_ROLE    = 1
    NURSE_ROLE  = 2
    DOCTOR_ROLE = 3
    ROLE_CHOICES = (
        (CHW_ROLE,    _('CHW')),
        (NURSE_ROLE,  _('Nurse')),
        (DOCTOR_ROLE, _('Doctor'))
    )
    user    = OneToOneField(User)
    mobile  = CharField(max_length=16, null=True)
    active  = BooleanField(default=True)
    role    = IntegerField(choices=ROLE_CHOICES, default=CHW_ROLE)
    clinic  = ForeignKey(Facility, null=True)
    manager = ForeignKey("Provider", null=True)

    @classmethod
    def by_mobile (cls, mobile):
        try:
            return cls.objects.get(mobile=mobile, active=True)
        except ObjectDoesNotExist:
            return None

class Case (Model):
    GENDER_CHOICES = (
        ('M', _('Male')), 
        ('F', _('Female')), 
    )
    UNKNOWN_STATUS  = 1
    HEALTHY_STATUS  = 2
    MILD_STATUS     = 3
    MODERATE_STATUS = 4
    SEVERE_STATUS   = 5
    INACTIVE_STATUS = 6
    DECEASED_STATUS = 7
    STATUS_CHOICES = (
        (UNKNOWN_STATUS,  _('Unknown')),
        (HEALTHY_STATUS,  _('Healthy')),
        (MILD_STATUS,     _('OTP')),
        (MODERATE_STATUS, _('MAM')),
        (SEVERE_STATUS,   _('SAM')),
        (INACTIVE_STATUS, _('Inactive')),
        (DECEASED_STATUS, _('Deceased'))  
    )
    ref_id      = IntegerField(_('Case ID #'), null=True)
    first_name  = CharField(max_length=255)
    last_name   = CharField(max_length=255)
    gender      = CharField(max_length=1, choices=GENDER_CHOICES)
    dob         = DateField(_('Date of Birth'))
    guardian    = CharField(max_length=255, null=True)
    mobile      = CharField(max_length=16, null=True)
    status      = IntegerField(choices=STATUS_CHOICES, default=HEALTHY_STATUS)
    provider    = ForeignKey(Provider)
    zone        = ForeignKey(Zone, null=True)
    village     = CharField(max_length=255, null=True)
    district    = CharField(max_length=255, null=True)
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)

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
        Model.save(self, *args)
        if not self.ref_id:
            self.ref_id = str(self._luhn(self.id))
            Model.save(self)
    
    def age (self):
        delta = datetime.datetime.now().date() - self.dob
        years = delta.days / 365.25
        if years > 3:
            return str(int(years))
        else:
            # FIXME: i18n
            return str(int(delta.days/30.4375))+"m"
        
class Report (Model):
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
    case        = ForeignKey(Case)
    provider    = ForeignKey(Provider)
    entered_at  = DateTimeField(auto_now_add=True)
    muac        = FloatField(_("MUAC (cm)"), null=True, blank=True)
    height      = FloatField(_("Height (cm)"), null=True, blank=True)
    weight      = FloatField(_("Weight (kg)"), null=True, blank=True)
    observed    = SeparatedValuesField(_("Observations"),
                    choices=OBSERVED_CHOICES, max_length=255,
                    blank=True, null=True)
    note        = TextField(blank=True,default="")

    def __unicode__ (self):
        return "#%d" % self.id

class MessageLog (Model):
    user        = ForeignKey(User)
    text        = CharField(max_length=255)
    was_handled = BooleanField(default=False)
