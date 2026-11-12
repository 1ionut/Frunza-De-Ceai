import os
from decimal import Decimal
from pathlib import Path
from random import Random

import django
from psycopg import ClientCursor
from psycopg.types.json import Jsonb


INSERT_CEAI = """INSERT INTO ceaiuri_ceai (
    nume, descriere, tara_origine, gramaj_g, pret, intensitate, ecologic,
    data_adaugare, recomandari_preparare, categorie_id
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    CURRENT_TIMESTAMP - make_interval(days => %s), %s,
    (SELECT id FROM ceaiuri_categorie WHERE slug = %s)
);"""


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    django.setup()

    from django.db import connection

    from ceaiuri.management.commands.populeaza_ceaiuri import CEAIURI
    from ceaiuri.models import Categorie, Ceai

    note = ("bergamotă", "coajă de portocală", "iasomie", "mentă", "piersică", "vanilie")
    gramaje = (25, 40, 50, 75, 100, 150, 200, 250)
    intensitati = [valoare for valoare, _ in Ceai._meta.get_field("intensitate").choices]

    variante = []
    for slug, categorie in Categorie.objects.order_by("slug").values_list("slug", "nume"):
        soiuri = [(nume, origine) for nume, tip, origine, *_ in CEAIURI if tip == categorie]
        for nume, origine in soiuri or [(categorie, None)]:
            variante.extend((nume, aroma, origine, slug) for aroma in note)
    if not variante:
        raise SystemExit("Adaugă cel puțin o categorie în admin înainte de a genera ceaiuri.")

    rng = Random(2026)
    rng.shuffle(variante)
    comenzi = ["BEGIN;"]
    with ClientCursor(connection.connection) as cursor:
        for index in range(50):
            nume, aroma, origine, slug = variante[index % len(variante)]
            valori = (
                f"{nume} cu note de {aroma}",
                f"Ceai cu note de {aroma}.",
                origine,
                rng.choice(gramaje),
                Decimal(rng.randint(1200, 9900)) / 100,
                rng.choice(intensitati),
                rng.choice((True, False)),
                rng.randint(0, 365),
                Jsonb([f"Infuzare {rng.randint(2, 6)} minute"]),
                slug,
            )
            comenzi.append(cursor.mogrify(INSERT_CEAI, valori))
    comenzi.append("COMMIT;")

    fisier = Path(__file__).with_name("ceaiuri_bonus.sql")
    fisier.write_text("\n\n".join(comenzi) + "\n", encoding="utf-8")
    print(f"Am scris 50 de comenzi INSERT în {fisier.resolve()}.")


if __name__ == "__main__":
    main()
