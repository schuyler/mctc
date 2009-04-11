from rapidsms.tests.scripted import TestScript
from app import App

class TestApp (TestScript):
    apps = (App,)
    # define your test scripts here.
    # e.g.:
    #
    # testRegister = """
    #   8005551212 > register as someuser
    #   8005551212 < Registered new user 'someuser' for 8005551212!
    #   8005551212 > tell anotheruser what's up??
    #   8005550000 < someuser said "what's up??"
    # """
    testJoin = """
        8005551212 > join smith john
        8005551212 < 8005551212 registered to *1 jsmith (SMITH, john).
        8005551212 > join smith john
        8005551212 < Username 'jsmith' is already in use. Reply with: JOIN <last> <first> <username>
        8005551212 > join smith john smithj
        8005551212 < Phone 8005551212 is already registered to SMITH, john. Reply with 'CONFIRM smithj'.   
        8005551212 > confirm smithj
        8005551212 < 8005551212 registered to *2 smithj (SMITH, john).
    """
