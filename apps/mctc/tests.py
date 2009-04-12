from rapidsms.tests.scripted import TestScript
from app import App
from datetime import datetime, date

def age_in_months (*ymd):
    return int((datetime.now().date() - date(*ymd)).days / 30.4375)    

def age_in_years (*ymd):
    return int((datetime.now().date() - date(*ymd)).days / 365.25)

class TestApp (TestScript):
    apps = (App,)

    testJoin = """
        # test registration
        1234567 > join smith john
        1234567 < 1234567 registered to *1 jsmith (SMITH, john).

        # test re-registration
        1234567 > join smith john
        1234567 < Username 'jsmith' is already in use. Reply with: JOIN <last> <first> <username>
    
        # test takeover/confirm
        1234567 > join smith john smithj
        1234567 < Phone 1234567 is already registered to SMITH, john. Reply with 'CONFIRM smithj'.   
        1234567 > confirm smithj
        1234567 < 1234567 registered to *2 smithj (SMITH, john).

        # test authentication
        7654321 > *2 can you read this?
        7654321 < 7654321 is not a registered number.

        # test direct messaging
        7654321 > join doe jane
        7654321 < 7654321 registered to *3 jdoe (DOE, jane).
        7654321 > *2 can you read this? 
        1234567 < *jdoe> can you read this?
        1234567 > *jdoe yes, I can read that
        7654321 < *smithj> yes, I can read that

        # test direct messaging to a non-existent user
        7654321 > *14 are you there?
        7654321 < User *14 is not registered.
        7654321 > *kdoe are you there?
        7654321 < User *kdoe is not registered.

        # FIXME: what happens if you message an inactive provider???
    """
    
    testNewCase = """
        7654321 > new madison dolly f 080411
        7654321 < New #18: MADISON, dolly F/%dm (None) None
    """ % age_in_months(2008,4,11)
