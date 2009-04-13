import rapidsms

from rapidsms.parsers.keyworder import Keyworder
from models import *

import re, time, datetime

def _(arg): return arg

def authenticated (func):
    def wrapper (self, message, *args):
        if message.sender:
            return func(self, message, *args)
        else:
            message.respond(_("%s is not a registered number.")
                            % message.peer)
            return True
    return wrapper

class HandlerFailed (Exception):
    pass

class App (rapidsms.app.App):
    MAX_MSG_LEN = 140
    keyword = Keyworder()

    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        provider = Provider.by_mobile(message.peer)
        if provider:
            message.sender = provider.user
        else:
            message.sender = None

    def handle (self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            return False
        try:
            return func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call 999-9999."))
            raise
        return True

    @keyword("join (\S+) (\S+) (\S+)(?: ([a-z]\w+))?")
    def join (self, message, code, last_name, first_name, username=None):
        try:
            clinic = Facility.objects.get(codename__iexact=code)
        except ObjectDoesNotExist:
            raise HandlerFailed(_("The given password is not recognized."))

        if username is None:
            # FIXME: this is going to run into charset issues
            username = (first_name[0] + last_name).lower()
        if User.objects.filter(username=username).count():
            raise HandlerFailed(_(
                "Username '%s' is already in use. " +
                "Reply with: JOIN <last> <first> <username>") % username)
        
        info = {
            "username"   : username,
            "first_name" : first_name.title(),
            "last_name"  : last_name.title()
        }
        user = User(**info)
        user.save()

        mobile = message.peer
        in_use = Provider.by_mobile(mobile)
        provider = Provider(mobile=mobile, user=user,
                            clinic=clinic, active=not bool(in_use))
        provider.save()
    
        if in_use:
            info.update({
                "last_name"  : in_use.user.last_name.upper(),
                "first_name" : in_use.user.first_name,
                "other"      : in_use.user.username,
                "mobile"     : mobile,
                "clinic"     : provider.clinic.name, 
            })
            message.respond(_(
                "Phone %(mobile)s is already registered to %(last_name)s, " +
                "%(first_name)s. Reply with 'CONFIRM %(username)s'.") % info)
        else:
            info.update({
                "id"        : user.id,
                "mobile"    : mobile,
                "clinic"    : provider.clinic.name, 
                "last_name" : last_name.upper()
            })
            self.respond_to_join(message, info)
        return True

    def respond_to_join(self, message, info):
        message.respond(
            _("%(mobile)s registered to *%(id)s %(username)s " +
              "(%(last_name)s, %(first_name)s) at %(clinic)s.") % info)

    @keyword(r'confirm (\w+)')
    def confirm_join (self, message, username):
        mobile   = message.peer
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            self.respond_not_registered(username)
        for provider in Provider.objects.filter(mobile=mobile):
            if provider.user.id == user.id:
                provider.active = True
            else:
                provider.active = False
            provider.save()
        info = {
            "first_name"    : user.first_name,
            "last_name"     : user.last_name.upper(),
            "id"            : user.id,
            "mobile"        : mobile,
            "clinic"        : provider.clinic.name,
            "username"      : username
        } 
        self.respond_to_join(message, info) 
        return True

    def respond_not_registered (self, message, target):
        raise HandlerFailed(_("User *%s is not registered.") % target)

    @keyword(r'\*(\w+) (.+)')
    @authenticated
    def direct_message (self, message, target, text):
        try:
            if re.match(r'^\d+$', target):
                user = User.objects.get(id=target)
            else:
                user = User.objects.get(username=target)
        except ObjectDoesNotExist:
            # FIXME: try looking up a group
            self.respond_not_registered(message, target)
        try:
            mobile = user.provider.mobile
        except:
            self.respond_not_registered(message, target)
        sender = message.sender.username
        return message.forward(mobile, "*%s> %s" % (sender, text))

    @keyword(r'new (\S+) (\S+) ([MF]) ([\d\-]+)( \D+)?( \d+)?')
    @authenticated
    def new_case (self, message, last, first, gender, dob,
                  guardian="", contact=""):
        provider = message.sender.provider
        zone     = None
        if provider.clinic:
            zone = provider.clinic.zone

        dob = re.sub(r'\D', '', dob)
        try:
            dob = time.strptime(dob, "%y%m%d")
        except ValueError:
            try:
                dob = time.strptime(dob, "%Y%m%d")
            except ValueError:
                raise HandlerFailed(_("Couldn't understand date: %s") % dob)
        dob = datetime.date(*dob[:3])
        if guardian:
            guardian = guardian.title()
        info = {
            "first_name" : first.title(),
            "last_name"  : last.title(),
            "gender"     : gender.upper()[0],
            "dob"        : dob,
            "guardian"   : guardian,
            "mobile"     : contact,
            "provider"   : provider,
            "zone"       : zone
        }

        ## TODO: check to see if the case already exists

        case = Case(**info)
        case.save()

        info.update({
            "id": case.ref_id,
            "last_name": last.upper(),
            "age": case.age()
        })
        if zone:
            info["zone"] = zone.name
        message.respond(_(
            "New #%(id)s: %(last_name)s, %(first_name)s %(gender)s/%(age)s " +
            "(%(guardian)s) %(zone)s") % info)
        return True

    def find_case (self, ref_id):
        try:
            return Case.objects.get(ref_id=int(ref_id))
        except ObjectDoesNotExist:
            raise HandlerFailed(_("Case #%s not found.") % ref_id)
 
    @keyword(r'cancel #?(\d+)')
    @authenticated
    def cancel_case (self, message, ref_id):
        case = self.find_case(ref_id)
        if case.report_set.count():
            raise HandlerFailed(_(
                "Cannot cancel #%s: case has diagnosis reports.") % ref_id)
        case.delete()
        message.respond(_("Case #%s cancelled.") % ref_id)
        return True


    @keyword(r'list(?: #)?')
    @authenticated
    def list_cases (self, message):
        cases = Case.objects.filter(provider=message.sender.provider)
        text  = ""
        for case in cases:
            item = "#%s %s %s. %s/%s" % (case.ref_id, case.last_name.upper(),
                case.first_name[0].upper(), case.gender, case.age())
            if len(text) + len(item) + 2 >= self.MAX_MSG_LEN:
                message.respond(text)
                text = ""
            if text: text += ", "
            text += item
        if text:
            message.respond(text)
        return True

    @keyword(r'list\s*\*')
    @authenticated
    def list_providers (self, message):
        providers = Provider.objects.all()
        text  = ""
        for provider in providers:
            item = "*%s %s" % (provider.user.id, provider.user.username)
            if len(text) + len(item) + 2 >= self.MAX_MSG_LEN:
                message.respond(text)
                text = ""
            if text: text += ", "
            text += item
        if text:
            message.respond(text)
        return True

    @keyword(r'#(\d+) ([\d\.]+) ([\d\.]+)( (?:\w\s*)+)?')
    @authenticated
    def report_case (self, message, ref_id, muac, weight, complications):
        case = self.find_case(ref_id)

        try:
            muac = float(muac)
        except ValueError:
            raise HandlerFailed(
                _("Can't understand MUAC (cm): %s") % muac)

        try:
            weight = float(weight)
        except ValueError:
            raise HandlerFailed(
                _("Can't understand weight (kg): %s") % weight)

        if muac > 30: # muac is in mm?
            muac /= 10.0

        if weight > 100: # muac is in g?
            weight /= 1000.0

        choices  = Report.OBSERVED_CHOICES 
        observed = []
        if complications:
            comp_list = dict([ (v[0].lower(), k) for k,v in choices ])
            complications = re.sub(r'\W+', '', complications)
            for observation in complications.lower():
                if observation not in comp_list:
                    raise HandlerFailed(_(
                        "Unknown observation code: %s" % observation))
                observed.append(comp_list[observation])
                
        report = Report(case=case, provider=message.sender.provider,
                        muac=muac, weight=weight, observed=observed)
        report.save()

        choice_term = dict(choices)
        info = {
            'ref_id'    : case.ref_id,
            'last'      : case.last_name.upper(),
            'first'     : case.first_name[0],
            'muac'      : "%.1f cm" % muac,
            'weight'    : "%.1f kg" % weight,
            'observed'  : ", ".join([choice_term[k] for k in observed])
        }
        msg = _("Report #%(ref_id)s: MUAC %(muac)s, wt. %(weight)s") % info
        if observed: msg += ", " + info["observed"]
        message.respond(msg)
        return True

