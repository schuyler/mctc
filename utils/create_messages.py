# note this requires the settings hack
import sys
import os
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

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