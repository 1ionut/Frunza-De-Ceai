from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .accesari import Accesare, accesari
from .models import Ceai


class LogTests(SimpleTestCase):
    def setUp(self):
        catalog = patch("ceaiuri.views.Ceai.objects.select_related", return_value=Ceai.objects.none())
        catalog.start()
        self.addCleanup(catalog.stop)
        accesari.clear()
        Accesare.ultimul_id = 0

    def tearDown(self):
        accesari.clear()
        Accesare.ultimul_id = 0

    def get(self, url):
        with redirect_stdout(StringIO()):
            return self.client.get(url, REMOTE_ADDR="192.0.2.10")

    def iduri_afisate(self, response):
        return [accesare.id for accesare in response.context["accesari"]]

    def pregateste_cinci_accesari(self):
        for url in ("/", "/info", "/despre", "/istoric", "/produse"):
            self.assertEqual(self.get(url).status_code, 200)

    def test_log_include_cererea_curenta_si_exclude_rutele_necunoscute(self):
        self.get("/")
        self.get("/info")
        response = self.get("/log")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.iduri_afisate(response), [1, 2, 3])
        self.assertEqual(accesari[-1].pagina(), "/log")
        self.assertEqual(self.get("/inexistent").status_code, 404)
        self.assertEqual(self.get("/static/inexistent.css").status_code, 404)
        self.assertEqual(len(accesari), 3)

    def test_ultimele_selecteaza_inclusiv_accesarea_log(self):
        self.get("/")
        self.get("/info")
        response = self.get("/log?ultimele=2")

        self.assertEqual(self.iduri_afisate(response), [2, 3])

    def test_ultimele_zero_nu_afiseaza_accesari(self):
        self.get("/")
        response = self.get("/log?ultimele=0")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.iduri_afisate(response), [])
        self.assertEqual(len(accesari), 2)

    def test_ultimele_invalid_afiseaza_eroare(self):
        for valoare in ("abc", "1.5", "-1", ""):
            with self.subTest(valoare=valoare):
                response = self.get("/log?ultimele=" + valoare)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["mesaj_eroare"])

    def test_ultimele_pre_mult_afiseaza_tot_si_mesajul_cerut(self):
        self.get("/")
        self.get("/info")
        response = self.get("/log?ultimele=50")

        self.assertEqual(self.iduri_afisate(response), [1, 2, 3])
        self.assertContains(response, "Exista doar 3 accesari fata de 50 accesari cerute")

    def test_numarul_total_nu_este_micsorat_de_filtre(self):
        self.get("/")
        self.get("/info")
        response = self.get("/log?accesari=nr&iduri=1&ultimele=1")

        self.assertEqual(response.context["mod_accesari"], "nr")
        self.assertEqual(response.context["total_accesari"], 3)
        self.assertEqual(self.iduri_afisate(response), [1])

    def test_iduri_repetate_pastreaza_ordinea_si_elimina_dublurile(self):
        self.pregateste_cinci_accesari()
        response = self.get("/log?iduri=2,3&iduri=5&iduri=4,2,1")

        self.assertEqual(self.iduri_afisate(response), [2, 3, 5, 4, 1])

    def test_dubluri_true_pastreaza_idurile_repetate(self):
        self.pregateste_cinci_accesari()
        response = self.get("/log?iduri=2,3&iduri=5&iduri=4,2,1&dubluri=true")

        self.assertEqual(self.iduri_afisate(response), [2, 3, 5, 4, 2, 1])

    def test_iduri_invalide_sau_inexistente_afiseaza_eroare(self):
        self.get("/")
        for valoare in ("abc", "9999", "1,abc", "1,,2"):
            with self.subTest(valoare=valoare):
                response = self.get("/log?iduri=" + valoare)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["mesaj_eroare"])

    def test_ultimele_se_aplica_dupa_selectia_idurilor(self):
        self.pregateste_cinci_accesari()
        response = self.get("/log?iduri=3,1,2&ultimele=2")

        self.assertEqual(self.iduri_afisate(response), [1, 2])

    def test_detalii_afiseaza_data_si_ora_in_lista(self):
        self.get("/")
        accesari[0].data = datetime(2025, 10, 2, 9, 5, 7,
                                    tzinfo=ZoneInfo("Europe/Bucharest"))
        response = self.get("/log?accesari=detalii&iduri=1")

        self.assertEqual(response.context["mod_accesari"], "detalii")
        self.assertContains(response, "<ul")
        self.assertContains(response, "02.10.2025")
        self.assertContains(response, "09:05:07")

    def test_parametri_numara_aparitiile_inclusiv_numele_repetate(self):
        response = self.get("/log?iduri=1&iduri=1&gol&accesari=nr")

        self.assertEqual(response.context["numar_parametri"], 4)
        self.assertEqual(response.context["parametri"],
                         ["iduri", "iduri", "gol", "accesari"])
        self.assertContains(response, "Parametri")
        self.assertIsNone(accesari[-1].parametri["gol"])

    def test_tabel_tot_afiseaza_toate_proprietatile(self):
        self.get("/info")
        response = self.get("/log?tabel=tot&iduri=1")

        self.assertEqual(response.context["coloane"],
                         ["id", "ip_client", "url", "parametri", "data", "pagina"])
        self.assertContains(response, "<table")
        self.assertContains(response, "192.0.2.10")
        self.assertContains(response, "http://testserver/info")

    def test_tabel_selecteaza_coloane_si_protejeaza_textul_html(self):
        self.get("/info?mesaj=%3Cscript%3Ealert(1)%3C/script%3E")
        response = self.get("/log?tabel=id,url,parametri&iduri=1")

        self.assertEqual(response.context["coloane"], ["id", "url", "parametri"])
        self.assertContains(response, "<table")
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_coloane_necunoscute_nu_provoaca_eroare_de_server(self):
        for valoare in ("__class__", "id,secret"):
            with self.subTest(valoare=valoare):
                response = self.get("/log?tabel=" + valoare)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["mesaj_eroare"])
                self.assertNotIn("__class__", response.context["coloane"])

    def test_statisticile_includ_paginile_nevizitate(self):
        for numar in range(3):
            self.get("/info")
        response = self.get("/log?ultimele=0")

        self.assertEqual(response.context["numar_maxim"], 3)
        self.assertIn("/info", response.context["pagina_maxima"])
        self.assertEqual(response.context["numar_minim"], 0)
        self.assertIn("/despre", response.context["pagina_minima"])

    def test_pagina_unei_accesari_si_id_inexistent(self):
        self.get("/info?test=valoare")
        response = self.get("/accesare1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "192.0.2.10")
        self.assertContains(response, "http://testserver/info?test=valoare")
        self.assertContains(response, "valoare")
        self.assertEqual(self.get("/accesare9999").status_code, 404)
        self.assertEqual(self.get("/accesareabc").status_code, 404)

    def test_pagini_folosesc_baza_footer_meniu_si_fisiere_statice(self):
        rute = ("/", "/info", "/log", "/despre", "/istoric",
                "/produse", "/contact", "/cos_virtual")
        for ruta in rute:
            with self.subTest(ruta=ruta):
                response = self.get(ruta)
                self.assertEqual(response.status_code, 200)
                nume_template = [template.name for template in response.templates]
                self.assertTrue(any(nume and nume.endswith("baza.html")
                                    for nume in nume_template))
                self.assertContains(response, "<header")
                self.assertContains(response, "<main")
                self.assertContains(response, "<footer")
                self.assertContains(response, "192.0.2.10")
                self.assertContains(response, "Frunză de Ceai")
                for destinatie in rute:
                    self.assertContains(response, 'href="' + destinatie + '"')
                html = response.content.decode()
                self.assertRegex(html, r'href="[^"]*/static/[^"]*nav\.css"')
                if ruta in ("/", "/despre"):
                    self.assertRegex(html, r'<img\b[^>]*src="/static/')
                    minim_sectiuni = 5 if ruta == "/" else 2
                    self.assertGreaterEqual(html.count("<section"), minim_sectiuni)
                if ruta in ("/contact", "/cos_virtual"):
                    self.assertContains(response, "In lucru")
