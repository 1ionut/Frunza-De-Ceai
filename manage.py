import os
import sys

from django.core.management import execute_from_command_line

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    execute_from_command_line(sys.argv)
