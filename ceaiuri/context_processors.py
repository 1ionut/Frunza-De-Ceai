from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings

def date_firma(request):
    return {
        "firma": settings.FIRMA,
        "an_curent": datetime.now(ZoneInfo(settings.TIME_ZONE)).year,
    }
