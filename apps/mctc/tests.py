from rapidsms.tests.scripted import TestScript
from django.core.management import call_command
from app import App
from models import Case, User
from datetime import datetime, date

def age_in_months (*ymd):
    return int((datetime.now().date() - date(*ymd)).days / 30.4375)    

def age_in_years (*ymd):
    return int((datetime.now().date() - date(*ymd)).days / 365.25)

class TestApp (TestScript):
    fixtures = ('test.json',)
    apps = (App,)

    def setUp (self):
        # borrowed from django/test/testcases.py
        call_command('loaddata', *self.fixtures, **{'verbosity': 0})
        TestScript.setUp(self)

    test_00_Join = """
        # test registration
        1234567 > join apple smith john
        1234567 < 1234567 registered to *1 jsmith (SMITH, John) at Alphaville.

        # test re-registration
        1234567 > join apple smith john
        1234567 < Username 'jsmith' is already in use. Reply with: JOIN <last> <first> <username>
    
        # test takeover/confirm
        1234567 > join banana smith john smithj
        1234567 < Phone 1234567 is already registered to SMITH, John. Reply with 'CONFIRM smithj'.   
        1234567 > confirm smithj
        1234567 < 1234567 registered to *2 smithj (SMITH, John) at Bravo Town.

        # test authentication
        7654321 > *2 can you read this?
        7654321 < 7654321 is not a registered number.

        # test direct messaging
        7654321 > join cherry doe jane
        7654321 < 7654321 registered to *3 jdoe (DOE, Jane) at Charliesburg.
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

    caseAges = (
        age_in_months(2008,4,11),
        age_in_years(2005,4,11),
        age_in_months(2009,2,11),
        age_in_months(2007,6,15),)
    
    test_00_NewCase = """
        # test basic case creation
        7654321 > new madison dolly f 080411
        7654321 < New #18: MADISON, Dolly F/%dm (None) Whiskey

        # case with guardian and age in years
        7654321 > new madison molly f 20050411 sally
        7654321 < New #26: MADISON, Molly F/%d (Sally) Whiskey

        # case with guardian and phone number
        7654321 > new madison holly f 090211 sally 230123
        7654321 < New #34: MADISON, Holly F/%dm (Sally) Whiskey

        # case with phone number but no guardian
        7654321 > new madison wally m 070615 230123
        7654321 < New #42: MADISON, Wally M/%dm (None) Whiskey

        # FIXME: unparsable cases???
    """ % caseAges

    def test_01_CreatedCases (self):
        user = User.objects.get(username="jdoe")
        case = Case.objects.get(ref_id=42)
        self.assertEqual(case.mobile, "230123", "case 42 mobile")
        self.assertEqual(case.provider, user.provider, "case 42 provider")

        case = Case.objects.get(ref_id=34)
        self.assertEqual(case.mobile, "230123", "case 34 mobile")
        self.assertEqual(case.guardian, "Sally", "case 34 guardian")
        self.assertEqual(case.provider, user.provider, "case 34 provider")

    test_01_ListCases = """
        0000000 > list
        0000000 < 0000000 is not a registered number.

        7654321 > list
        7654321 < #18 MADISON D. F/%dm, #26 MADISON M. F/%d, #34 MADISON H. F/%dm, #42 MADISON W. M/%dm
    """ % caseAges

    test_01_ListProviders = """
        0000000 > list *
        0000000 < 0000000 is not a registered number.

        7654321 > list *
        7654321 < *1 jsmith, *2 smithj, *3 jdoe
    """
    
    test_02_CancelCases = """
        0000000 > cancel #34
        0000000 < 0000000 is not a registered number.
        
        7654321 > cancel #34
        7654321 < Case #34 cancelled.
        7654321 > cancel 42
        7654321 < Case #42 cancelled. 
        7654321 > cancel 42
        7654321 < Case #42 not found. 
    """ 

    test_03_ReportCase = """
        # basic test
        7654321 > #26 7.5 21
        7654321 < Report #26: MUAC 7.5 cm, wt. 21.0 kg 

        # mm get converted to cm, g to kg
        7654321 > #26 75.5 2150
        7654321 < Report #26: MUAC 7.5 cm, wt. 2.1 kg 

        # TODO: check weight delta over previous report and see if it's
        # within a plausible range

        # complications list
        7654321 > #26 75.5 21 e a d
        7654321 < Report #26: MUAC 7.5 cm, wt. 21.0 kg, Edema, Appetite Loss, Diarrhea

        # more complications, formatted differently
        7654321 > #26 75.5 21 hcv
        7654321 < Report #26: MUAC 7.5 cm, wt. 21.0 kg, High Fever, Chronic Cough, Vomiting

        # one last complication test
        7654321 > #26 75.5 21 u
        7654321 < Report #26: MUAC 7.5 cm, wt. 21.0 kg, Unresponsive

        # MUAC fail
        7654321 > #26 45.5.5 83.1 foo
        7654321 < Can't understand MUAC (cm): 45.5.5

        # weight fail
        7654321 > #26 45 83.1.1 foo
        7654321 < Can't understand weight (kg): 83.1.1

        # complication fail
        7654321 > #26 800 23 NOT WELL
        7654321 < Unknown observation code: n
    """

    def test_zzz_queue_is_empty (self):
        self.assertFalse(self.backend.message_waiting)

