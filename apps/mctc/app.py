import rapidsms

from rapidsms.parsers.keyworder import Keyworder
from models import *

class App (rapidsms.app.App):
    keyword = Keyworder()

    def start (self):
        """Configure your app in the start phase."""
        pass

    def handle(self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            return False
        return func(self, message, *captures)

    @keyword("join (\S+) (\S+)(?: (\S+))?")
    def join (self, message, last_name, first_name, username=None):
        if username is None:
            username = (last_name + first_name[0]).lower()
        info = {
            "username"   : username,
            "first_name" : first_name,
            "last_name"  : last_name
        }
        user = User(**info)
        user.save()
        provider = Provider(mobile = message.caller, user = user) 
        provider.save()
        info["id"]        = user.id
        info["mobile"]    = message.caller
        info["last_name"] = last_name.upper()
        message.respond(
            _("%(mobile)s registered to *%(id)s %(username)s " +
              "(%(last_name)s, %(first_name)s)") % info)

    @keyword(r'\*(\w+) (.+)')
    def direct_message (self, message, target, text):
        pass
