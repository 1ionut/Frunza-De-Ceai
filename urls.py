from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("ceaiuri.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Administrare Frunză de Ceai"
admin.site.site_title = "Frunză de Ceai"
admin.site.index_title = "Catalogul și sediile firmei"
