from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from random import Random

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from psycopg import ClientCursor
from psycopg.types.json import Jsonb

from ceaiuri.models import Categorie, Ceai

from .populeaza_ceaiuri import CEAIURI


INSERT_CEAI = """INSERT INTO ceaiuri_ceai (
    nume, descriere, tara_origine, gramaj_g, pret, intensitate, ecologic,
    data_adaugare, recomandari_preparare, categorie_id
)
SELECT %s, %s, %s, %s, %s, %s, %s,
       CURRENT_TIMESTAMP - make_interval(days => %s), %s,
       (SELECT id FROM ceaiuri_categorie WHERE slug = %s)
WHERE NOT EXISTS (SELECT 1 FROM ceaiuri_ceai WHERE nume = %s);"""

NOTE = ("bergamotă", "coajă de portocală", "iasomie", "mentă", "piersică", "vanilie")
GRAMAJE = (25, 40, 50, 75, 100, 150, 200, 250)


class Command(BaseCommand):
    help = "Generează comenzi SQL INSERT pentru un lot aleator de ceaiuri."

    def add_arguments(self, parser):
        parser.add_argument("--numar", type=int, default=50, help="Numărul de ceaiuri generate.")
        parser.add_argument("--seed", type=int, help="Valoare pentru a reproduce același lot.")
        parser.add_argument("--fisier", type=Path, help="Calea fișierului SQL scris în UTF-8.")

    def handle(self, *args, numar, seed, fisier, **options):
        if numar < 1:
            raise CommandError("Numărul de ceaiuri trebuie să fie cel puțin 1.")
        if connection.vendor != "postgresql":
            raise CommandError("Generatorul produce comenzi SQL pentru PostgreSQL.")

        categorii = list(Categorie.objects.order_by("slug").values_list("slug", "nume"))
        if not categorii:
            raise CommandError("Adaugă cel puțin o categorie înainte de a genera ceaiuri.")

        profiluri = defaultdict(list)
        for nume, categorie, origine, *_ in CEAIURI:
            profiluri[categorie].append((nume, origine))

        rng = Random(seed)
        lot = f"{rng.getrandbits(48):012x}"
        intensitati = [valoare for valoare, _ in Ceai._meta.get_field("intensitate").choices]
        rng.shuffle(categorii)

        # Tranzacția aplică lotul integral. Blocarea evită dublurile dacă același lot se importă simultan.
        comenzi = ["BEGIN;", "LOCK TABLE ceaiuri_ceai IN SHARE ROW EXCLUSIVE MODE;"]
        with ClientCursor(connection.connection) as cursor:
            for index in range(numar):
                slug, categorie = categorii[index % len(categorii)]
                baza, origine = rng.choice(profiluri[categorie] or [(categorie, None)])
                nota = rng.choice(NOTE)
                nume = f"{baza} cu note de {nota} · lot {lot}-{index + 1:03d}"
                gramaj = rng.choice(GRAMAJE)
                pret = Decimal(rng.randint(8 * gramaj + 800, 22 * gramaj + 2000)) / 100
                recomandari = [
                    f"Apă la {rng.choice((75, 80, 85, 90, 95))}°C",
                    f"Infuzare {rng.randint(2, 6)} minute",
                ]
                valori = (
                    nume,
                    f"{categorie}, cu note de {nota}. Pachet de {gramaj} g.",
                    origine,
                    gramaj,
                    pret,
                    rng.choice(intensitati),
                    rng.choice((True, False)),
                    rng.randint(0, 365),
                    Jsonb(recomandari),
                    slug,
                    nume,
                )
                comenzi.append(cursor.mogrify(INSERT_CEAI, valori))
        comenzi.append("COMMIT;")

        script = "\n\n".join(comenzi) + "\n"
        if fisier is None:
            self.stdout.write(script)
        else:
            fisier.write_text(script, encoding="utf-8")
            self.stdout.write(f"Am generat {numar} comenzi INSERT în {fisier}.")
