# utils/logging_utils.py
import sys
from django.apps import apps

def skip_logging_during_migration() -> bool:
    return not apps.ready or 'migrate' in sys.argv or 'makemigrations' in sys.argv
