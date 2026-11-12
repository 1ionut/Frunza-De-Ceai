from pathlib import Path
from random import Random


INSERT = """INSERT INTO ceaiuri_ceai (
    nume, descriere, tara_origine, gramaj_g, pret, intensitate, ecologic,
    data_adaugare, recomandari_preparare, categorie_id
) VALUES (
    '{nume}', 'Ceai cu note de {aroma}.', '{origine}', {gramaj}, {pret:.2f},
    '{intensitate}', {ecologic}, CURRENT_TIMESTAMP - INTERVAL '{zile} days',
    '["Infuzare {minute} minute"]',
    (SELECT id FROM ceaiuri_categorie WHERE slug = '{categorie}')
);"""

# Soi, țară de origine și slugul categoriei din baza de date.
SOIURI = [
    ("Sencha", "Japonia", "ceai-verde"),
    ("Gunpowder", "China", "ceai-verde"),
    ("Assam", "India", "ceai-negru"),
    ("Earl Grey", "Sri Lanka", "ceai-negru"),
    ("Bai Mu Dan", "China", "ceai-alb"),
    ("Silver Needle", "China", "ceai-alb"),
    ("Tie Guan Yin", "China", "ceai-oolong"),
    ("Dong Ding", "Taiwan", "ceai-oolong"),
    ("Rooibos", "Africa de Sud", "infuzii-plante-fructe"),
    ("Infuzie de hibiscus", "România", "infuzii-plante-fructe"),
]
AROME = ["bergamotă", "iasomie", "mentă", "piersică", "portocală", "vanilie"]


def main():
    rng = Random(2026)
    combinatii = [(soi, aroma) for soi in SOIURI for aroma in AROME]
    comenzi = ["BEGIN;"]
    for (soi, origine, categorie), aroma in rng.sample(combinatii, 50):
        comenzi.append(INSERT.format(
            nume=f"{soi} cu note de {aroma}",
            aroma=aroma,
            origine=origine,
            categorie=categorie,
            gramaj=rng.choice([25, 50, 75, 100, 150, 200, 250]),
            pret=rng.randint(1200, 9900) / 100,
            intensitate=rng.choice(["delicata", "echilibrata", "puternica"]),
            ecologic=rng.choice(["TRUE", "FALSE"]),
            zile=rng.randint(0, 365),
            minute=rng.randint(2, 6),
        ))
    comenzi.append("COMMIT;")
    fisier = Path(__file__).with_name("ceaiuri_bonus.sql")
    fisier.write_text("\n\n".join(comenzi) + "\n", encoding="utf-8")
    print(f"Am scris 50 de comenzi INSERT în {fisier.name}.")


if __name__ == "__main__":
    main()
