#
# note this requires the settings hack
import sys
import os
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

for model, file in (
    ["mctc.observation", "observations.json"],
    ["mctc.diagnosis", "diagnoses.json"],
    ["mctc.diagnosiscategory", "diagnoses_categories.json"],    
    ["mctc.lab", "lab_codes.json"],        
    ):
    cmd = 'python "%s/django-manage.py" dumpdata %s  --indent=2 > "%s/apps/mctc/models/fixtures/%s"'
    os.system(cmd % (path, model, path, file))
