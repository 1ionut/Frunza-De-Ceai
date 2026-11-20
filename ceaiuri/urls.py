from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.urls import path, re_path, reverse_lazy

from . import conturi, views

app_name = "ceaiuri"

urlpatterns = [
    path("", views.index, name="index"),
    path("inregistrare", conturi.formular_date, name="inregistrare"),
    path("autentificare", conturi.autentificare, name="autentificare"),
    path("deconectare", LogoutView.as_view(next_page="ceaiuri:index"), name="deconectare"),
    path("profil", conturi.profil, name="profil"),
    path("profil/modifica", conturi.modifica_date, name="modifica_date"),
    path("profil/parola", login_required(
        PasswordChangeView.as_view(
            template_name="ceaiuri/formular_cont.html", extra_context={"titlu": "Schimbă parola"},
            success_url=reverse_lazy("ceaiuri:profil"),
        ), login_url="ceaiuri:autentificare",
    ), name="schimba_parola"),
    path("info", views.info, name="info"),
    path("log", views.log, name="log"),
    path("despre", views.despre, name="despre"),
    path("istoric", views.istoric, name="istoric"),
    path("produse", views.produse, name="produse"),
    path("categorii/<slug:slug>", views.produse, name="categorie"),
    path("produs/<int:id>", views.produs, name="produs"),
    path("contact", views.in_lucru, {"nume_pagina": "Contact"}, name="contact"),
    path("cos_virtual", views.in_lucru, {"nume_pagina": "Coș virtual"}, name="cos_virtual"),
    re_path(r"^accesare(?P<id>[0-9]+)$", views.accesare, name="accesare"),
]
