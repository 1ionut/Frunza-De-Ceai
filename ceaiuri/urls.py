from django.urls import path, re_path

from . import views

app_name = "ceaiuri"

urlpatterns = [
    path("", views.index, name="index"),
    path("info", views.info, name="info"),
    path("log", views.log, name="log"),
    path("despre", views.despre, name="despre"),
    path("istoric", views.istoric, name="istoric"),
    path("produse", views.produse, name="produse"),
    path("produs/<int:id>", views.produs, name="produs"),
    path("contact", views.in_lucru, {"nume_pagina": "Contact"}, name="contact"),
    path("cos_virtual", views.in_lucru, {"nume_pagina": "Coș virtual"}, name="cos_virtual"),
    re_path(r"^accesare(?P<id>[0-9]+)$", views.accesare, name="accesare"),
]
