# takes the csv and converts it into json, this allows them to maintain csv.. which is 
# i presume easier than json
from django.utils import simplejson as json
import csv

import sys
import os
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

file = os.path.join(path, "apps", "mctc", "models", "fixtures", "diagnostic_code_categories.csv")

from apps.mctc.models.reports import DiagnosisCategory, Diagnosis

if "--force" not in sys.argv and Diagnosis.objects.count():
    print """Warning: there are already diagnosis in the db, this will add more. 
This might cause duplicates. Are you sure about that?

If so pass repeat this command with --force at the end"""
    sys.exit(1)

count = 0
reader = csv.reader(open(file))
for row in reader:
    d = DiagnosisCategory()
    d.name = row[1]
    d.id = row[0]
    d.save()
    count += 1

print "Added or overrode %s diagnosis category" % count

file = os.path.join(path, "apps", "mctc", "models", "fixtures", "diagnostic_icd9_codes.csv")

count = 0
header = False
reader = csv.reader(open(file))
for row in reader:
    if not header: 
        header = True
        continue
        
    d = Diagnosis()
    d.code = row[1]
    category = DiagnosisCategory.objects.get(id=int(row[0]))
    d.category = category
    d.name = row[2]
    d.mvp_code = row[3]
    d.save()
    count += 1

print "Added %s to diagnosis" % count

    