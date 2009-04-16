from django.db.models import *
from django.contrib.auth.models import User
from fields import SeparatedValuesField
import md5

def _(arg): return arg

class Zone (Model):
    def __unicode__ (self): return self.name
    number  = PositiveIntegerField(unique=True,db_index=True)
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
    zone        = ForeignKey(Zone,db_index=True)
    codename    = CharField(max_length=255,unique=True,db_index=True)
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
    mobile  = CharField(max_length=16, null=True, db_index=True)
    role    = IntegerField(choices=ROLE_CHOICES, default=CHW_ROLE)
    active  = BooleanField(default=True)
    alerts  = BooleanField(default=False, db_index=True)
    clinic  = ForeignKey(Facility, null=True, db_index=True)
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
    ref_id      = IntegerField(_('Case ID #'), null=True, db_index=True)
    first_name  = CharField(max_length=255, db_index=True)
    last_name   = CharField(max_length=255, db_index=True)
    gender      = CharField(max_length=1, choices=GENDER_CHOICES)
    dob         = DateField(_('Date of Birth'))
    guardian    = CharField(max_length=255, null=True, blank=True)
    mobile      = CharField(max_length=16, null=True, blank=True)
    status      = IntegerField(choices=STATUS_CHOICES,
                               default=HEALTHY_STATUS, db_index=True)
    provider    = ForeignKey(Provider, db_index=True)
    zone        = ForeignKey(Zone, null=True, db_index=True)
    village     = CharField(max_length=255, null=True, blank=True)
    district    = CharField(max_length=255, null=True, blank=True)
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
            self.ref_id = self._luhn(self.id)
            Model.save(self)
    
    def age (self):
        delta = datetime.datetime.now().date() - self.dob
        years = delta.days / 365.25
        if years > 3:
            return str(int(years))
        else:
            # FIXME: i18n
            return str(int(delta.days/30.4375))+"m"

    @classmethod
    def filter_active (cls):
        return cls.objects.filter(status__le=cls.CURED_STATUS)

class Report (Model):
    class Meta:
        get_latest_by = 'entered_at'

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
    case        = ForeignKey(Case, db_index=True)
    provider    = ForeignKey(Provider, db_index=True)
    entered_at  = DateTimeField(auto_now_add=True, db_index=True)
    muac        = IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height      = IntegerField(_("Height (cm)"), null=True, blank=True)
    weight      = FloatField(_("Weight (kg)"), null=True, blank=True)
    observed    = SeparatedValuesField(_("Observations"),
                    choices=OBSERVED_CHOICES, max_length=255,
                    null=True, blank=True)

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

class CaseNote (Model):
    case        = ForeignKey(Case, related_name="notes", db_index=True)
    created_by  = ForeignKey(User, db_index=True)
    created_at  = DateTimeField(auto_now_add=True, db_index=True)
    text        = TextField()

class MessageLog (Model):
    mobile      = CharField(max_length=255, db_index=True)
    sent_by     = ForeignKey(User, null=True)
    text        = CharField(max_length=255)
    was_handled = BooleanField(default=False, db_index=True)
    created_at  = DateTimeField(auto_now_add=True, db_index=True)
