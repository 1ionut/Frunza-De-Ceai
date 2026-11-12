from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404, QueryDict
from django.shortcuts import get_object_or_404, render
from .accesari import accesari, formateaza_data_romana, Accesare
from .models import Ceai

DESCRIERE = (
    "Frunză de Ceai este un magazin online de ceaiuri vrac. "
    "Proiectul va prezenta ceaiuri verzi, negre, albe și oolong, cu informații "
    "despre origine, arome, gramaj, preț și modul de preparare. Clienții vor "
    "putea consulta catalogul, filtra produsele și, în etapele următoare, adăuga ceaiurile "
    "în coș și plasa comenzi."
)

PAGINI = {
    "/": "Acasă",
    "/info": "Informații despre server",
    "/log": "Jurnalul accesărilor",
    "/despre": "Despre noi",
    "/istoric": "Istoric",
    "/produse": "Produse",
    "/contact": "Contact",
    "/cos_virtual": "Coș virtual",
}

COLOANE_CATALOG = {
    "nume": "Nume",
    "pret": "Preț",
    "gramaj_g": "Gramaj",
    "data_adaugare": "Data adăugării",
    "stoc": "Stoc",
}


def index(request):
    return render(request, "ceaiuri/index.html", {"descriere": DESCRIERE})


def info(request):
    data = request.accesare.data
    optiune = request.GET.get("data", "")
    if optiune == "zi":
        #text = data.strftime("%d.%m.%y")
        text = request.accesare.calculeaza_data(data=data)
    elif optiune == "timp":
        text = data.strftime("%H:%M:%S")
    else:
        text = formateaza_data_romana(data) + ', ' + data.strftime("%H:%M:%S")
    return render(request, "ceaiuri/info.html", {"text_data": text})


def despre(request):
    return render(request, "ceaiuri/despre.html")


def istoric(request):
    return render(request, "ceaiuri/istoric.html")


def produse(request):
    parametri = QueryDict(mutable=True)
    coloana = request.GET.get("coloana", "nume")
    parametri["coloana"] = coloana if coloana in COLOANE_CATALOG else "nume"
    parametri["sort"] = "d" if request.GET.get("sort") == "d" else "a"
    prefix = "-" if parametri["sort"] == "d" else ""
    ceaiuri = Ceai.objects.select_related("categorie")
    taguri = list(dict.fromkeys(tag for tag in request.GET.getlist("tag") if tag))
    if taguri:
        parametri.setlist("tag", taguri)
        ceaiuri = ceaiuri.filter(taguri__contains=taguri)
    paginator = Paginator(ceaiuri.order_by(prefix + parametri["coloana"], "pk"), 5)
    pagina = paginator.get_page(request.GET.get("pagina", 1))
    context = {
        "produse": pagina,
        "numere_pagini": range(1, paginator.num_pages + 1),
        "parametri_catalog": parametri,
        "coloane_catalog": COLOANE_CATALOG,
        "taguri_active": taguri,
    }
    return render(request, "ceaiuri/produse.html", context)


def produs(request, id):
    ceaiuri = Ceai.objects.select_related("categorie").prefetch_related("arome", "raioane__sediu")
    try:
        ceai = get_object_or_404(ceaiuri, pk=id)
    except Http404:
        return render(request, "ceaiuri/produs_inexistent.html", status=404)

    similare = Ceai.objects.filter(categorie=ceai.categorie).exclude(pk=ceai.pk)
    return render(request, "ceaiuri/produs.html", {
        "produs": ceai,
        "similare": similare.order_by("?")[:settings.PRODUSE_SIMILARE],
    })


def in_lucru(request, nume_pagina):
    return render(request, "ceaiuri/in_lucru.html", {"nume_pagina": nume_pagina})


def log(request):
    toate = accesari[:]
    selectate = toate
    mesaj_eroare = ""

    if "iduri" in request.GET:
        selectate = []
        iduri = []
        dubluri = request.GET.get("dubluri", "false") == "true"
        for grup in request.GET.getlist("iduri"):
            for text_id in grup.split(","):
                try:
                    id_cautat = int(text_id)
                    if id_cautat < 1:
                        raise ValueError
                except ValueError:
                    mesaj_eroare += "ID invalid: " + text_id + ". "
                    continue

                if id_cautat in iduri and not dubluri:
                    continue
                iduri.append(id_cautat)

                gasita = False
                for acces in toate:
                    if acces.id == id_cautat:
                        selectate.append(acces)
                        gasita = True
                        break
                if not gasita:
                    mesaj_eroare += f"Nu exista accesarea cu id-ul {id_cautat}. "

    if "ultimele" in request.GET:
        try:
            numar = int(request.GET["ultimele"])
            if numar < 0:
                raise ValueError
        except ValueError:
            mesaj_eroare += "Parametrul ultimele trebuie sa fie un numar intreg nenegativ. "
            selectate = []
        else:
            if numar > len(selectate):
                mesaj_eroare += (
                    f"Exista doar {len(selectate)} accesari fata de {numar} accesari cerute"
                )
            elif numar == 0:
                selectate = []
            else:
                selectate = selectate[-numar:]

    parametri = []
    for nume, valori in request.GET.lists():
        for valoare in valori:
            parametri.append(nume)

    proprietati = ["id", "ip_client", "url", "parametri", "data", "pagina"]
    coloane = []
    if "tabel" in request.GET:
        if request.GET["tabel"] == "tot":
            coloane = proprietati
        else:
            for nume in request.GET["tabel"].split(","):
                nume = nume.strip()
                if nume not in proprietati:
                    mesaj_eroare += "Coloana necunoscuta: " + nume + ". "
                elif nume not in coloane:
                    coloane.append(nume)

    randuri = []
    if coloane:
        for acces in selectate:
            valori = {
                "id": acces.id,
                "ip_client": acces.ip_client,
                "url": acces.url,
                "parametri": acces.lista_parametri(),
                "data": acces.data.strftime("%d.%m.%Y %H:%M:%S"),
                "pagina": acces.pagina(),
            }
            rand = []
            for nume in coloane:
                rand.append(valori[nume])
            randuri.append(rand)

    numere = {}
    for cale in PAGINI:
        numere[cale] = 0
    for acces in toate:
        cale = acces.pagina()
        if cale not in numere:
            numere[cale] = 0
        numere[cale] += 1

    numar_minim = len(toate)
    numar_maxim = 0
    for cale in numere:
        if numere[cale] < numar_minim:
            numar_minim = numere[cale]
        if numere[cale] > numar_maxim:
            numar_maxim = numere[cale]

    pagina_minima = ""
    pagina_maxima = ""
    for cale in numere:
        nume = PAGINI.get(cale, "Detalii accesare") + " (" + cale + ")"
        if numere[cale] == numar_minim:
            if pagina_minima != "":
                pagina_minima += ", "
            pagina_minima += nume
        if numere[cale] == numar_maxim:
            if pagina_maxima != "":
                pagina_maxima += ", "
            pagina_maxima += nume

    context = {
        "accesari": selectate,
        "mesaj_eroare": mesaj_eroare,
        "mod_accesari": request.GET.get("accesari", ""),
        "total_accesari": len(toate),
        "parametri": parametri,
        "numar_parametri": len(parametri),
        "coloane": coloane,
        "randuri": randuri,
        "pagina_minima": pagina_minima,
        "pagina_maxima": pagina_maxima,
        "numar_minim": numar_minim,
        "numar_maxim": numar_maxim,
    }
    return render(request, "ceaiuri/log.html", context)


def accesare(request, id):
    try:
        id = int(id)
    except ValueError:
        raise Http404("ID invalid.")
    for acces in accesari:
        if acces.id == id:
            return render(request, "ceaiuri/accesare.html", {"accesare": acces})
    raise Http404("Nu exista o accesare cu acest id.")
