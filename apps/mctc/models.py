from django.db.models import *
from django.contrib.auth.models import User
import md5

def _(arg): return arg

class Zone (Model):
    name    = CharField(max_length=255)
    lon     = FloatField(blank=True)
    lat     = FloatField(blank=True)

class Facility (Model):
    CLINIC_ROLE  = 1
    DISTRIB_ROLE = 2
    ROLE_CHOICES = (
        (CLINIC_ROLE,  _('Clinic')),
        (DISTRIB_ROLE, _('Distribution Point')),
    )
    name    = CharField(max_length=255)
    role    = IntegerField(choices=ROLE_CHOICES, default=CLINIC_ROLE)
    zone    = ForeignKey(Zone)
    lon     = FloatField(blank=True)
    lat     = FloatField(blank=True)

class Provider (Model):
    CHW_ROLE    = 1
    NURSE_ROLE  = 2
    DOCTOR_ROLE = 3
    ROLE_CHOICES = (
        (CHW_ROLE,    _('CHW')),
        (NURSE_ROLE,  _('Nurse')),
        (DOCTOR_ROLE, _('Doctor'))
    )
    user    = OneToOneField(User)
    mobile  = CharField(max_length=16, blank=True)
    active  = BooleanField(default=True)
    role    = IntegerField(choices=ROLE_CHOICES, default=CHW_ROLE)
    clinic  = ForeignKey(Facility, blank=True)
    manager = ForeignKey("Provider", blank=True)

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
    ref_id      = IntegerField(_('Case ID #'), unique=True, blank=True)
    first_name  = CharField(max_length=255)
    last_name   = CharField(max_length=255)
    gender      = CharField(max_length=1, choices=GENDER_CHOICES)
    dob         = DateField(_('Date of Birth'))
    guardian    = CharField(max_length=255, blank=True)
    mobile      = CharField(max_length=16, blank=True)
    status      = IntegerField(choices=STATUS_CHOICES, default=HEALTHY_STATUS)
    provider    = ForeignKey(User)
    zone        = ForeignKey(Zone, blank=True)
    village     = CharField(max_length=255, blank=True)
    district    = CharField(max_length=255, blank=True)
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)

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
            return str(years)
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
    UNCONSCIOUS_OBSERVED   = 7
    OBSERVED_CHOICES = (
        (EDEMA_OBSERVED,         _("Edema")),
        (APPETITE_LOSS_OBSERVED, _("Appetite Loss")),
        (DIARRHEA_OBSERVED,      _("Diarrhea")),
        (VOMITING_OBSERVED,      _("Vomiting")),
        (CHRONIC_COUGH_OBSERVED, _("Chronic Cough")),
        (HIGH_FEVER_OBSERVED,    _("High Fever")),
        (UNCONSCIOUS_OBSERVED,   _("Unconscious/Unresponsive")),
    )
    case        = ForeignKey(Case)
    provider    = ForeignKey(User)
    entered_at  = DateTimeField(auto_now_add=True)
    muac        = FloatField(_("MUAC (cm)"), blank=True)
    height      = FloatField(_("Height (cm)"), blank=True)
    weight      = FloatField(_("Weight (kg)"), blank=True)
    observed    = CommaSeparatedIntegerField(_("Observations"),
                    choices=OBSERVED_CHOICES, max_length=255, blank=True)
    note        = TextField(blank=True)

class MessageLog (Model):
    user        = ForeignKey(User)
    text        = CharField(max_length=255)
    was_handled = BooleanField(default=False)
