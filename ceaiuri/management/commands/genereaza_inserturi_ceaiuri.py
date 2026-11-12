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
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    CURRENT_TIMESTAMP - make_interval(days => %s), %s,
    (SELECT id FROM ceaiuri_categorie WHERE slug = %s)
);"""

NOTE = ("bergamotă", "coajă de portocală", "iasomie", "mentă", "piersică", "vanilie")
GRAMAJE = (25, 40, 50, 75, 100, 150, 200, 250)


class Command(BaseCommand):
    help = "Generează comenzi SQL INSERT pentru ceaiuri aleatoare."

    def add_arguments(self, parser):
        parser.add_argument("--numar", type=int, default=50, help="Numărul de ceaiuri generate.")
        parser.add_argument("--seed", type=int, default=2026, help="Schimbă selecția aleatoare.")
        parser.add_argument("--fisier", type=Path, default=Path("ceaiuri_bonus.sql"), help="Fișierul SQL rezultat.")

    def handle(self, *args, numar, seed, fisier, **options):
        if numar < 1:
            raise CommandError("Numărul de ceaiuri trebuie să fie cel puțin 1.")
        if connection.vendor != "postgresql":
            raise CommandError("Generatorul produce comenzi SQL pentru PostgreSQL.")

        variante = []
        for slug, categorie in Categorie.objects.order_by("slug").values_list("slug", "nume"):
            soiuri = [(nume, origine) for nume, tip, origine, *_ in CEAIURI if tip == categorie]
            for nume, origine in soiuri or [(categorie, None)]:
                variante.extend((nume, nota, origine, slug) for nota in NOTE)
        if not variante:
            raise CommandError("Adaugă cel puțin o categorie înainte de a genera ceaiuri.")

        rng = Random(seed)
        rng.shuffle(variante)
        intensitati = [valoare for valoare, _ in Ceai._meta.get_field("intensitate").choices]

        comenzi = ["BEGIN;"]
        with ClientCursor(connection.connection) as cursor:
            for index in range(numar):
                nume, nota, origine, slug = variante[index % len(variante)]
                valori = (
                    f"{nume} cu note de {nota}",
                    f"Ceai cu note de {nota}.",
                    origine,
                    rng.choice(GRAMAJE),
                    Decimal(rng.randint(1200, 9900)) / 100,
                    rng.choice(intensitati),
                    rng.choice((True, False)),
                    rng.randint(0, 365),
                    Jsonb([f"Infuzare {rng.randint(2, 6)} minute"]),
                    slug,
                )
                comenzi.append(cursor.mogrify(INSERT_CEAI, valori))
        comenzi.append("COMMIT;")

        fisier.write_text("\n\n".join(comenzi) + "\n", encoding="utf-8")
        self.stdout.write(f"Am generat {numar} comenzi INSERT în {fisier.resolve()}.")
