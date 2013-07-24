from django.conf import settings
import os.path
execfile(os.path.join(settings.ENHYDRIS_PROGRAM_DIR, 'urls-base.py'))
