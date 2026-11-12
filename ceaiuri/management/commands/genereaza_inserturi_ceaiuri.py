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
SELECT %(nume)s, %(descriere)s, %(origine)s, %(gramaj)s, %(pret)s, %(intensitate)s, %(ecologic)s,
       CURRENT_TIMESTAMP - make_interval(days => %(zile)s), %(recomandari)s,
       (SELECT id FROM ceaiuri_categorie WHERE slug = %(slug)s)
WHERE NOT EXISTS (SELECT 1 FROM ceaiuri_ceai WHERE nume = %(nume)s);"""

NOTE = ("bergamotă", "coajă de portocală", "iasomie", "mentă", "piersică", "vanilie")
GRAMAJE = (25, 40, 50, 75, 100, 150, 200, 250)


class Command(BaseCommand):
    help = "Generează comenzi SQL INSERT pentru un lot aleator de ceaiuri."

    def add_arguments(self, parser):
        parser.add_argument("--numar", type=int, default=50, help="Numărul de ceaiuri generate.")
        parser.add_argument("--seed", type=int, default=2026, help="Schimbă lotul generat.")
        parser.add_argument("--fisier", type=Path, default=Path("ceaiuri_bonus.sql"), help="Fișierul SQL rezultat.")

    def handle(self, *args, numar, seed, fisier, **options):
        if numar < 1:
            raise CommandError("Numărul de ceaiuri trebuie să fie cel puțin 1.")
        if connection.vendor != "postgresql":
            raise CommandError("Generatorul produce comenzi SQL pentru PostgreSQL.")

        categorii = list(Categorie.objects.order_by("slug").values_list("slug", "nume"))
        if not categorii:
            raise CommandError("Adaugă cel puțin o categorie înainte de a genera ceaiuri.")

        rng = Random(seed)
        lot = f"{rng.getrandbits(48):012x}"
        intensitati = [valoare for valoare, _ in Ceai._meta.get_field("intensitate").choices]
        rng.shuffle(categorii)

        # Aplică întregul lot într-o tranzacție și evită importurile simultane.
        comenzi = ["BEGIN;", "LOCK TABLE ceaiuri_ceai IN SHARE ROW EXCLUSIVE MODE;"]
        with ClientCursor(connection.connection) as cursor:
            for index in range(numar):
                slug, categorie = categorii[index % len(categorii)]
                profiluri = [
                    (nume, origine)
                    for nume, tip, origine, *_ in CEAIURI
                    if tip == categorie
                ]
                baza, origine = rng.choice(profiluri or [(categorie, None)])
                nota = rng.choice(NOTE)
                gramaj = rng.choice(GRAMAJE)
                pret_bani = rng.randint(8 * gramaj + 800, 22 * gramaj + 2000)
                temperatura = rng.choice((75, 80, 85, 90, 95))
                minute = rng.randint(2, 6)
                valori = {
                    "nume": f"{baza} cu note de {nota} · lot {lot}-{index + 1:03d}",
                    "descriere": f"{categorie}, cu note de {nota}. Pachet de {gramaj} g.",
                    "origine": origine,
                    "gramaj": gramaj,
                    "pret": Decimal(pret_bani) / 100,
                    "intensitate": rng.choice(intensitati),
                    "ecologic": rng.choice((True, False)),
                    "zile": rng.randint(0, 365),
                    "recomandari": Jsonb([f"Apă la {temperatura}°C", f"Infuzare {minute} minute"]),
                    "slug": slug,
                }
                comenzi.append(cursor.mogrify(INSERT_CEAI, valori))
        comenzi.append("COMMIT;")

        fisier.write_text("\n\n".join(comenzi) + "\n", encoding="utf-8")
        self.stdout.write(f"Am generat {numar} comenzi INSERT în {fisier.resolve()}.")
