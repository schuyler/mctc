from django.test import TestCase
from django.contrib.auth.models import User, Group
from table import Table

class request:
    def __init__(self):
        self.GET = {}

class table(TestCase):
    fixtures = ["overall.json",]
    
    def testUser(self):
        req = request()
        table = Table(req, "user", User.objects.all(), "user_head.html", "user_body.html")
        print table()
        req.GET["page_user"] = 3
        table = Table(req, "user", User.objects.all(), "user_head.html", "user_body.html")
        print table()        