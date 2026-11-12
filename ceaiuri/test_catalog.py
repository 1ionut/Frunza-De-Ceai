from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Categorie, Ceai


@override_settings(PROD_PER_PAG=2, STOC_MIN=5, PRODUSE_SIMILARE=2)
class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.verde = Categorie.objects.create(
            nume="Ceai verde", slug="ceai-verde", descriere="Ceaiuri cu note vegetale.",
            culoare="#4C7A45", sigla="🍃",
        )
        negru = Categorie.objects.create(nume="Ceai negru", slug="ceai-negru", descriere="Ceaiuri oxidate.")
        cls.goala = Categorie.objects.create(nume="Categorie fără produse", slug="fara-produse", descriere="Test de meniu.")
        for index in range(1, 5):
            cls.ceai = Ceai.objects.create(
                nume=f"Ceai verde {index}", categorie=cls.verde, pret=10 * index,
                gramaj_g=100, stoc=index, taguri=["mentă", "proaspăt"] if index < 4 else ["mentă"],
            )
        Ceai.objects.create(
            nume="Ceai negru cu mentă", categorie=negru, pret=100,
            gramaj_g=50, stoc=9, taguri=["mentă", "proaspăt"],
        )

    def test_taguri_cumulative_sortare_si_paginare_in_categorie(self):
        adresa = self.verde.get_absolute_url()
        parametri = {"sort": "d", "coloana": "pret", "tag": ["mentă", "proaspăt"]}
        raspuns = self.client.get(adresa, parametri)
        self.assertTemplateUsed(raspuns, "ceaiuri/produse.html")
        pagina = raspuns.context["produse"]
        self.assertEqual(pagina.paginator.count, 3)
        self.assertEqual([ceai.pret for ceai in pagina], [Decimal("30"), Decimal("20")])
        self.assertContains(raspuns, "Pagina 1 din 2", count=2)
        self.assertContains(raspuns, "Se afișează produsele între 1 și 2 din totalul de 3 produse.")
        self.assertContains(raspuns, "tag=ment%C4%83&amp;tag=proasp%C4%83t&amp;pagina=2")
        self.assertContains(raspuns, f'{adresa}?coloana=pret&amp;sort=d&amp;tag=proasp%C4%83t')
        self.assertContains(raspuns, 'style="--culoare-categorie: #4C7A45;"')
        self.assertContains(raspuns, "Ceaiuri cu note vegetale.")

        urmatoarea = self.client.get(adresa, {**parametri, "pagina": 2})
        self.assertEqual([ceai.pret for ceai in urmatoarea.context["produse"]], [Decimal("10")])

        un_tag = self.client.get(adresa, {**parametri, "tag": "mentă", "pagina": 2})
        self.assertContains(un_tag, f'href="{adresa}?coloana=pret&amp;sort=d&amp;tag=ment%C4%83&amp;tag=proasp%C4%83t"')

    def test_catalog_general_si_meniu_din_baza_de_date(self):
        raspuns = self.client.get(reverse("ceaiuri:produse"), {"coloana": "pret", "sort": "d", "tag": "mentă"})
        self.assertEqual(raspuns.context["produse"].paginator.count, 5)
        self.assertEqual([ceai.pret for ceai in raspuns.context["produse"]], [Decimal("100"), Decimal("40")])
        self.assertContains(raspuns, "Categorii")
        self.assertContains(raspuns, self.verde.get_absolute_url())
        self.assertNotContains(raspuns, self.goala.get_absolute_url())
        self.assertContains(raspuns, "Imagine indisponibilă")
        self.assertContains(raspuns, "Stoc limitat")
        pagina_goala = self.client.get(self.goala.get_absolute_url())
        self.assertContains(pagina_goala, "Se afișează 0 produse.")

    def test_detalii_recomandari_si_produs_inexistent(self):
        raspuns = self.client.get(self.ceai.get_absolute_url())
        self.assertContains(raspuns, "Produse din aceeași categorie")
        self.assertContains(raspuns, 'href="/produse?tag=ment%C4%83"')
        self.assertContains(raspuns, self.verde.get_absolute_url())
        similare = list(raspuns.context["similare"])
        self.assertEqual(len(similare), 2)
        self.assertTrue(all(ceai.categorie == self.verde and ceai.pk != self.ceai.pk for ceai in similare))
        self.assertContains(
            self.client.get(reverse("ceaiuri:produs", kwargs={"id": 999999})),
            "Produsul căutat nu există.", status_code=404,
        )

    def test_imaginea_produsului_si_fisierul_lipsa(self):
        self.ceai.imagine = "ceaiuri/fotografie.jpg"
        self.ceai.save(update_fields=["imagine"])
        url = self.ceai.get_absolute_url()
        with patch.object(self.ceai.imagine.storage, "exists", return_value=True):
            self.assertContains(self.client.get(url), 'src="/media/ceaiuri/fotografie.jpg"')
        with patch.object(self.ceai.imagine.storage, "exists", return_value=False):
            raspuns = self.client.get(url)
            self.assertNotContains(raspuns, 'src="/media/ceaiuri/fotografie.jpg"')
            self.assertContains(raspuns, "Imagine indisponibilă")
