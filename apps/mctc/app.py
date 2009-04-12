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
        return func(self, message, *captures)

    @keyword("join (\S+) (\S+)(?: ([a-z]\w+))?")
    def join (self, message, last_name, first_name, username=None):
        if username is None:
            # FIXME: this is going to run into charset issues
            username = (first_name[0] + last_name).lower()
        if User.objects.filter(username=username).count():
            message.respond(_(
                "Username '%s' is already in use. " +
                "Reply with: JOIN <last> <first> <username>") % username)
            return True
        
        info = {
            "username"   : username,
            "first_name" : first_name,
            "last_name"  : last_name
        }
        user = User(**info)
        user.save()

        mobile = message.peer
        in_use = Provider.by_mobile(mobile)
        provider = Provider(mobile=mobile, user=user, active=not bool(in_use))
        provider.save()
    
        if in_use:
            info.update({
                "last_name"  : in_use.user.last_name.upper(),
                "first_name" : in_use.user.first_name,
                "other"      : in_use.user.username,
                "mobile"     : mobile,
            })
            message.respond(_(
                "Phone %(mobile)s is already registered to %(last_name)s, " +
                "%(first_name)s. Reply with 'CONFIRM %(username)s'.") % info)
        else:
            info.update({
                "id"        : user.id,
                "mobile"    : mobile,
                "last_name" : last_name.upper()
            })
            self.respond_to_join(message, info)
        return True

    def respond_to_join(self, message, info):
        message.respond(
            _("%(mobile)s registered to *%(id)s %(username)s " +
              "(%(last_name)s, %(first_name)s).") % info)

    @keyword(r'confirm (\w+)')
    def confirm_join (self, message, username):
        mobile   = message.peer
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return self.respond_not_registered(username)
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
            "username"      : username
        } 
        self.respond_to_join(message, info) 
        return True

    def respond_not_registered (self, message, target):
        message.respond(_("User *%s is not registered.") % target)
        return True

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
            return self.respond_not_registered(message, target)
        try:
            mobile = user.provider.mobile
        except:
            return self.respond_not_registered(message, target)
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
                # FIXME: parse failure
                return False
        dob = datetime.date(*dob[:3])
        info = {
            "first_name" : first,
            "last_name"  : last,
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

    def respond_case_not_found (self, message, ref_id):
        message.respond(_("Case #%s not found.") % ref_id)
        return True

    @keyword(r'cancel #?(\d+)')
    @authenticated
    def cancel_case (self, message, ref_id):
        try:
            case = Case.objects.get(ref_id=int(ref_id))
        except ObjectDoesNotExist:
            self.respond_case_not_found(message, ref_id)
        if case.diagnoses.count():
            message.respond(_(
                "Cannot cancel #%s: case has diagnosis reports.") % ref_id)
            return True
        case.delete()
        message.respond(_("Case #%s cancelled.") % ref_id)
        return True


    @keyword(r'list(?: #)?')
    @authenticated
    def list_cases (self, message):
        cases = Case.objects.filter(provider=message.sender.provider)
        text  = ""
        for case in cases:
            item = "#%s %s, %s %s/%s" % (case.ref_id, case.last_name.upper(),
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

