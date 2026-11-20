from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import DateUtilizator, Profil


class DateContForm(forms.ModelForm):
    first_name = forms.CharField(label="Prenume", max_length=150)
    last_name = forms.CharField(label="Nume", max_length=150)
    email = forms.EmailField(label="E-mail", max_length=254)

    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email"]
        field_classes = {"username": UsernameField}


class InregistrareForm(UserCreationForm, DateContForm):
    Meta = DateContForm.Meta


class DateUtilizatorForm(forms.ModelForm):
    class Meta:
        model = DateUtilizator
        fields = ["telefon", "tara", "judet", "localitate"]


class ProfilForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = ["strada", "cod_postal"]


class AutentificareForm(AuthenticationForm):
    tine_minte = forms.BooleanField(label="Ține-mă minte o zi", required=False)


def memoreaza_date(request):
    user = get_user_model().objects.select_related("dateutilizator", "profil").get(pk=request.user.pk)
    date = {
        "Utilizator": user.username, "Prenume": user.first_name, "Nume": user.last_name,
        "E-mail": user.email, "Înregistrat la": timezone.localtime(user.date_joined).strftime("%d.%m.%Y"),
    }
    for relatie, formular in [("dateutilizator", DateUtilizatorForm), ("profil", ProfilForm)]:
        obiect = getattr(user, relatie, None)
        if obiect is not None:
            for nume in formular.Meta.fields:
                valoare = getattr(obiect, nume)
                if valoare:
                    date[obiect._meta.get_field(nume).verbose_name.capitalize()] = valoare
    request.session["date_profil"] = date


def autentificare(request):
    date_post = request.POST if request.method == "POST" else None
    form = AutentificareForm(request, data=date_post)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        request.session.set_expiry(86400 if form.cleaned_data["tine_minte"] else 0)
        memoreaza_date(request)
        return redirect("ceaiuri:profil")
    return render(request, "ceaiuri/formular_cont.html", {"form": form, "titlu": "Autentificare"})


def formular_date(request, user=None):
    date_post = request.POST if request.method == "POST" else None
    tip_formular = InregistrareForm if user is None else DateContForm
    cont = tip_formular(date_post, instance=user)
    date = DateUtilizatorForm(date_post, instance=getattr(user, "dateutilizator", None))
    profil = ProfilForm(date_post, instance=getattr(user, "profil", None))
    if request.method == "POST" and all([cont.is_valid(), date.is_valid(), profil.is_valid()]):
        with transaction.atomic():
            utilizator = cont.save(commit=False)
            utilizator.save(update_fields=DateContForm.Meta.fields if user is not None else None)
            date.instance.utilizator = utilizator
            date.save()
            if any(profil.cleaned_data.values()):
                profil.instance.utilizator = utilizator
                profil.save()
            elif user is not None:
                Profil.objects.filter(utilizator=user).delete()
        if user is None:
            return redirect("ceaiuri:autentificare")
        memoreaza_date(request)
        return redirect("ceaiuri:profil")
    return render(request, "ceaiuri/formular_cont.html", {
        "titlu": "Înregistrare" if user is None else "Modifică datele",
        "form": cont, "date_form": date, "profil_form": profil,
    })


@login_required(login_url="ceaiuri:autentificare")
def modifica_date(request):
    return formular_date(request, request.user)


@login_required(login_url="ceaiuri:autentificare")
def profil(request):
    if "date_profil" not in request.session:
        memoreaza_date(request)
    return render(request, "ceaiuri/profil.html", {"date": request.session["date_profil"]})
