#
# note this requires the settings hack
import sys
import os
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

os.system('python "%s/django-manage.py" dumpdata mctc.observation --indent=2 > "%s/apps/mctc/fixtures/observations.json"' % (path, path))
os.system('python "%s/django-manage.py" dumpdata mctc.diagnosis --indent=2 > "%s/apps/mctc/fixtures/diagnoses.json"' % (path, path))