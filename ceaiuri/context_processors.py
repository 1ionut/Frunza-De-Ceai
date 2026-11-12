from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings

from .models import Categorie

def date_firma(request):
    return {
        "firma": settings.FIRMA,
        "an_curent": datetime.now(ZoneInfo(settings.TIME_ZONE)).year,
    }


def categorii_meniu(request):
    return {"categorii_meniu": Categorie.objects.filter(ceaiuri__isnull=False).distinct()}
