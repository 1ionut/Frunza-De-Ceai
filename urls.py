from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, reverse_lazy

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("ceaiuri.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Frunză de Ceai · Administrare"
admin.site.site_title = "Administrare | Frunză de Ceai"
admin.site.index_title = "Administrarea magazinului"
admin.site.site_url = reverse_lazy("ceaiuri:index")
