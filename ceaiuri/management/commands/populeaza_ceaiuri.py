from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from ceaiuri.models import Categorie, Ceai


CATEGORII = [
    ("Ceai verde", "Ceaiuri cu note vegetale, proaspete și delicate.", "#4C7A45"),
    ("Ceai negru", "Ceaiuri cu gust intens și arome bogate.", "#563B2B"),
    ("Ceai alb", "Ceaiuri fine, cu note florale și gust delicat.", "#D8CBA8"),
    ("Ceai oolong", "Ceaiuri parțial oxidate, cu arome florale sau prăjite.", "#B27A3F"),
    ("Infuzii de plante și fructe", "Amestecuri aromate de plante, flori și fructe.", "#A34258"),
]

# Nume, categorie, origine, gramaj, preț, ecologic, descriere.
CEAIURI = [
    ("Sencha", "Ceai verde", "Japonia", 100, "29.90", True,
     "Ceai verde cu note vegetale și gust proaspăt. Potrivit pentru o pauză de dimineață."),
    ("Gunpowder", "Ceai verde", "China", 100, "24.50", False,
     "Frunze rulate în mici perle, cu aromă intensă și note ușor afumate."),
    ("Jasmine Green", "Ceai verde", "China", 50, "22.00", False,
     "Ceai verde parfumat cu flori de iasomie, cu un gust floral delicat."),
    ("Assam", "Ceai negru", "India", 100, "27.90", False,
     "Ceai negru corpolent, cu note de malț. Se poate servi simplu sau cu lapte."),
    ("Darjeeling", "Ceai negru", "India", 50, "32.50", True,
     "Ceai negru cu aromă fină, note florale și accente de struguri."),
    ("Earl Grey", "Ceai negru", "Sri Lanka", 100, "31.00", False,
     "Amestec de ceai negru aromatizat cu bergamotă, cu note citrice."),
    ("Bai Mu Dan", "Ceai alb", "China", 50, "34.90", True,
     "Ceai alb din muguri și frunze tinere, cu note florale și dulceață discretă."),
    ("Silver Needle", "Ceai alb", "China", 30, "49.90", False,
     "Ceai alb din muguri argintii, cu infuzie deschisă la culoare și gust fin."),
    ("White Peony cu piersică", "Ceai alb", "China", 50, "36.50", False,
     "Amestec de ceai alb și bucăți de piersică, cu aromă fructată și delicată."),
    ("Tie Guan Yin", "Ceai oolong", "China", 50, "39.90", False,
     "Oolong cu note de orhidee și gust catifelat, potrivit pentru infuzii succesive."),
    ("Dong Ding", "Ceai oolong", "Taiwan", 50, "42.00", True,
     "Oolong cu note prăjite, accente de nuci și un final ușor dulce."),
    ("Milky Oolong", "Ceai oolong", "Taiwan", 100, "58.90", False,
     "Oolong cu profil cremos și note dulci, pentru o infuzie aromată și rotundă."),
    ("Rooibos cu vanilie", "Infuzii de plante și fructe", "Africa de Sud", 100, "28.50", True,
     "Infuzie de rooibos cu vanilie, fără cofeină, cu gust dulceag și aromă caldă."),
    ("Mentă și lămâie", "Infuzii de plante și fructe", "România", 50, "18.90", True,
     "Amestec de mentă și coajă de lămâie, cu aromă proaspătă. Se poate servi și rece."),
    ("Fructe de pădure", "Infuzii de plante și fructe", "România", 100, "26.00", False,
     "Amestec de hibiscus, măceșe, mere și fructe de pădure, cu gust dulce-acrișor."),
]


class Command(BaseCommand):
    help = "Adaugă categorii și ceaiuri fictive pentru demonstrații, fără a dubla datele la rerulare."

    @transaction.atomic
    def handle(self, *args, **options):
        categorii = {}
        categorii_noi = 0
        ceaiuri_noi = 0
        for nume, descriere, culoare in CATEGORII:
            categorie, creat = Categorie.objects.get_or_create(
                nume=nume,
                defaults={
                    "slug": slugify(nume),
                    "descriere": descriere,
                    "culoare": culoare,
                    "sigla": "ceaiuri/imagini/frunze.svg",
                    "vizibila": True,
                },
            )
            categorii[nume] = categorie
            categorii_noi += int(creat)

        for nume, categorie, origine, gramaj, pret, ecologic, descriere in CEAIURI:
            _, creat = Ceai.objects.get_or_create(
                nume=nume,
                categorie=categorii[categorie],
                gramaj_g=gramaj,
                defaults={
                    "descriere": descriere,
                    "tara_origine": origine,
                    "pret": Decimal(pret),
                    "ecologic": ecologic,
                },
            )
            ceaiuri_noi += int(creat)

        self.stdout.write(self.style.SUCCESS(
            f"Adăugate: {categorii_noi} categorii și {ceaiuri_noi} ceaiuri. "
            f"Total: {Categorie.objects.count()} categorii și {Ceai.objects.count()} ceaiuri."
        ))
