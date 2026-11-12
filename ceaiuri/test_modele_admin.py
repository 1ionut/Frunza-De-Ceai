from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Aroma, Categorie, Ceai, Raion, Sediu


class ModeleSiAdministrareTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categorie = Categorie.objects.create(
            nume="Ceai verde", slug="ceai-verde", descriere="Frunze neoxidate."
        )
        cls.sediu = Sediu.objects.create(
            nume="Magazin central", adresa="Strada Frunzelor 10"
        )
        cls.raion = Raion.objects.create(
            sediu=cls.sediu, cod_raion="R1", nume="Ceaiuri verzi"
        )
        cls.administrator = get_user_model().objects.create_superuser(
            username="admin_test", password="ParolaDoarPentruTeste_93!"
        )

    def creeaza_ceai(self, **modificari):
        date = {
            "nume": "Sencha",
            "categorie": self.categorie,
            "gramaj_g": 50,
            "pret": Decimal("24.50"),
        }
        date.update(modificari)
        return Ceai.objects.create(**date)

    def formular_admin(self, model, date=None, fisiere=None):
        cerere = RequestFactory().get("/admin/")
        cerere.user = self.administrator
        formular = admin.site._registry[model].get_form(cerere)
        return formular(data=date, files=fisiere)

    def date_formular_ceai(self, **modificari):
        date = {
            "nume": "Sencha",
            "categorie": str(self.categorie.pk),
            "gramaj_g": "50",
            "pret": "24.50",
            "intensitate": "echilibrata",
            "data_adaugare_0": "2026-11-04",
            "data_adaugare_1": "10:30:00",
            "recomandari_preparare": "",
        }
        date.update(modificari)
        return date

    def test_restrictiile_protejeaza_baza_si_fara_formular(self):
        # objects.create nu apelează full_clean: aceste erori sunt oprite de DB.
        for modificari in (
            {"gramaj_g": 0},
            {"pret": Decimal("0.00")},
            {"pret": Decimal("-1.00")},
            {"intensitate": "necunoscuta"},
        ):
            with self.subTest(modificari=modificari):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    self.creeaza_ceai(**modificari)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categorie.objects.create(
                nume="Culoare greșită", slug="culoare-gresita",
                descriere="Exemplu", culoare="verde",
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categorie.objects.create(nume="", slug="nume-gol", descriere="Exemplu")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Raion.objects.create(sediu=self.sediu, cod_raion="", nume="Exemplu")

    def test_slug_este_unic_in_baza_si_are_mesaj_in_formular(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categorie.objects.create(
                nume="Alt ceai verde", slug="ceai-verde", descriere="Exemplu"
            )
        formular = self.formular_admin(Categorie, {
            "nume": "Alt ceai verde", "slug": "ceai-verde", "descriere": "Exemplu",
            "culoare": "#52734D", "sigla": "fa-solid fa-leaf", "vizibila": "on",
        })
        self.assertFalse(formular.is_valid())
        self.assertIn(
            "Există deja o categorie cu acest identificator.", formular.errors["slug"]
        )

    def test_codul_raionului_este_unic_doar_in_acelasi_sediu(self):
        alt_sediu = Sediu.objects.create(nume="Magazin nord", adresa="Strada Nordului 2")
        alt_raion = Raion.objects.create(
            sediu=alt_sediu, cod_raion="R1", nume="Ceaiuri negre"
        )
        self.assertNotEqual(alt_raion.pk, self.raion.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Raion.objects.create(sediu=self.sediu, cod_raion="R1", nume="Duplicat")

    def test_stergerea_sediului_sterge_raioanele_si_expunerile(self):
        ceai = self.creeaza_ceai()
        ceai.raioane.add(self.raion)
        self.sediu.delete()
        self.assertFalse(Raion.objects.filter(pk=self.raion.pk).exists())
        self.assertTrue(Ceai.objects.filter(pk=ceai.pk).exists())
        self.assertFalse(ceai.raioane.exists())

    def test_categoria_cu_produse_nu_poate_fi_stearsa(self):
        self.creeaza_ceai()
        with self.assertRaises(ProtectedError):
            self.categorie.delete()
        self.assertTrue(Categorie.objects.filter(pk=self.categorie.pk).exists())

    def test_aromele_si_raioanele_se_asociaza_many_to_many(self):
        primul = self.creeaza_ceai()
        al_doilea = self.creeaza_ceai(nume="Jasmine Green")
        floral = Aroma.objects.create(nume="Florală")
        citric = Aroma.objects.create(nume="Citrică")
        alt_raion = Raion.objects.create(
            sediu=self.sediu, cod_raion="R2", nume="Selecții parfumate"
        )
        primul.arome.add(floral, citric)
        al_doilea.arome.add(floral)
        primul.raioane.add(self.raion, alt_raion)
        al_doilea.raioane.add(self.raion)
        self.assertEqual(primul.arome.count(), 2)
        self.assertEqual(floral.ceaiuri.count(), 2)
        self.assertEqual(primul.raioane.count(), 2)
        self.assertEqual(self.raion.ceaiuri.count(), 2)

    def test_vectorul_de_recomandari_accepta_numai_texte_nevide(self):
        ceai = self.creeaza_ceai()
        for valoare in ({}, {"apa": 80}, [80], [""], ["  "], "Apă la 80°C"):
            with self.subTest(valoare=valoare):
                ceai.recomandari_preparare = valoare
                with self.assertRaises(ValidationError):
                    ceai.full_clean()
        for valoare in ([], ["Apă la 80°C", "Infuzare 3 minute"]):
            with self.subTest(valoare=valoare):
                ceai.recomandari_preparare = valoare
                ceai.full_clean()

    def test_campul_admin_gol_salveaza_vectorul_gol(self):
        formular = self.formular_admin(Ceai, self.date_formular_ceai())
        self.assertTrue(formular.is_valid(), formular.errors)
        ceai = formular.save()
        ceai.refresh_from_db()
        self.assertEqual(ceai.recomandari_preparare, [])

    def test_admin_respinge_json_care_nu_reprezinta_vector_de_texte(self):
        for valoare in ("{}", '{"apa": 80}', "[80]", '[""]'):
            with self.subTest(valoare=valoare):
                formular = self.formular_admin(
                    Ceai, self.date_formular_ceai(recomandari_preparare=valoare)
                )
                self.assertFalse(formular.is_valid())
                self.assertIn("recomandari_preparare", formular.errors)

    def test_listele_default_sunt_independente_si_data_include_ora(self):
        primul = Ceai()
        al_doilea = Ceai()
        primul.recomandari_preparare.append("Infuzare 3 minute")
        self.assertEqual(al_doilea.recomandari_preparare, [])
        self.assertIsNotNone(primul.data_adaugare.tzinfo)
        ceai = self.creeaza_ceai()
        ceai.refresh_from_db()
        self.assertIsNotNone(ceai.data_adaugare.tzinfo)

    def test_admin_cere_autentificare_si_listeaza_toate_entitatile(self):
        index = reverse("admin:index")
        raspuns = self.client.get(index)
        self.assertRedirects(raspuns, reverse("admin:login") + "?next=" + index)
        self.assertTrue(self.client.login(
            username="admin_test", password="ParolaDoarPentruTeste_93!"
        ))
        raspuns = self.client.get(index)
        self.assertEqual(raspuns.status_code, 200)
        for nume in ("Categorii", "Ceaiuri", "Arome", "Sedii", "Raioane"):
            self.assertContains(raspuns, nume)
        for model in (Categorie, Ceai, Aroma, Sediu, Raion):
            with self.subTest(model=model.__name__):
                url = reverse(f"admin:ceaiuri_{model._meta.model_name}_add")
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_help_text_si_mesajul_max_length_sunt_vizibile_in_admin(self):
        self.client.force_login(self.administrator)
        url = reverse("admin:ceaiuri_ceai_add")
        raspuns = self.client.get(url)
        for text in (
            "Greutatea netă, în grame, a pachetului vândut, nu a unei porții.",
            "Prețul în lei al întregului pachet, cu cel mult două zecimale.",
            "Intensitatea degustată a produsului; nu se deduce automat din categorie.",
        ):
            self.assertContains(raspuns, text)
        raspuns = self.client.post(url, self.date_formular_ceai(nume="x" * 201))
        self.assertEqual(raspuns.status_code, 200)
        self.assertContains(
            raspuns, "Denumirea ceaiului poate avea cel mult 200 de caractere."
        )
        self.assertFalse(Ceai.objects.exists())

    def test_lab4_pret_evidentiat_in_lista_admin(self):
        admin_ceai = admin.site._registry[Ceai]
        self.assertIn("pret_evidentiat", admin_ceai.list_display)
        self.assertNotIn("pret", admin_ceai.list_display)
        self.assertEqual(admin_ceai.pret_evidentiat.admin_order_field, "pret")
        self.assertEqual(admin_ceai.pret_evidentiat.short_description, "Preț evidențiat")

        ceai = self.creeaza_ceai()
        rezultat = str(admin_ceai.pret_evidentiat(ceai))
        self.assertIn('<strong style="color: #2e7d32;">', rezultat)
        self.assertIn("24.50 lei</strong>", rezultat)

        self.client.force_login(self.administrator)
        raspuns = self.client.get(reverse("admin:ceaiuri_ceai_changelist"))
        self.assertContains(raspuns, "Preț evidențiat")
        self.assertContains(raspuns, "24.50 lei")
