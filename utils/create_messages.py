# a simple way to pump messages into the system in bulk

import sys
import os
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['RAPIDSMS_INI'] = os.path.join(path, "rapidsms.ini")
os.environ['DJANGO_SETTINGS_MODULE'] = 'rapidsms.webui.settings'

from apps.mctc.models import MessageLog
from apps.mctc.models import User
user = User.objects.all()[0]

for x in range(0, 50):
    msg = MessageLog()
    msg.mobile = "283475347658234756"
    msg.sent_by = user
    msg.text = "this is a test"
    msg.was_handled = True
    msg.save()

print "created 50 msgs"