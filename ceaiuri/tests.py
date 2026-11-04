from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from .accesari import Accesare, formateaza_data_romana
from .views import DESCRIERE


class AccesareTests(SimpleTestCase):
    def setUp(self):
        self.accesare = Accesare("127.0.0.1", "http://localhost/info?data=zi&a=")
        self.accesare.data = datetime(2025, 10, 2, 9, 5, 7,
                                      tzinfo=ZoneInfo("Europe/Bucharest"))

    def test_id_data_si_dictionare_independente(self):
        alta = Accesare("127.0.0.2", "http://localhost/")
        self.assertGreater(alta.id, self.accesare.id)
        self.assertIsInstance(alta.data, datetime)
        self.accesare.parametri["a"] = "1"
        self.assertEqual(alta.parametri, {})

    def test_url_pagina_si_parametri(self):
        self.assertEqual(self.accesare.string_url(), "http://localhost/info?data=zi&a=")
        self.assertEqual(self.accesare.pagina(), "/info")
        self.accesare.parametri = {"data": "zi", "a": "", "b": None}
        self.assertEqual(self.accesare.lista_parametri(),
                         [("data", "zi"), ("a", None), ("b", None)])

    def test_formatare_romana_si_procente_literale(self):
        self.assertEqual(formateaza_data_romana(self.accesare.data),
                         "Joi, 2 Octombrie 2025")
        self.assertEqual(formateaza_data_romana(self.accesare.data, "%%A %B %Y"),
                         "%A Octombrie 2025")

    def test_variante_sectiune_data(self):
        self.assertIn("Joi, 2 Octombrie 2025, 09:05:07", self.accesare.calculeaza_data())
        zi = self.accesare.calculeaza_data(data="zi")
        self.assertIn("2 Octombrie 2025", zi)
        self.assertNotIn("09:05:07", zi)
        timp = self.accesare.calculeaza_data(data="timp")
        self.assertIn("09:05:07", timp)
        self.assertNotIn("Octombrie", timp)
        self.assertEqual(self.accesare.calculeaza_data(data="altceva"),
                         self.accesare.calculeaza_data())
        self.assertIn("2025/10/2", self.accesare.calculeaza_data("%Y/%m/%d"))

    def test_str_contine_toate_campurile(self):
        text = str(self.accesare)
        for camp in ("id", "ip_client", "string_url", "pagina",
                     "calculeaza_data", "lista_parametri"):
            self.assertIn(camp + ": ", text)


class PaginiTests(SimpleTestCase):
    def test_pagini_middleware_si_loguri_fara_baza_de_date(self):
        for url in ("/", "/info", "/info?data=zi", "/info?data=timp", "/info?data="):
            with self.subTest(url=url), redirect_stdout(StringIO()) as consola:
                response = self.client.get(url, REMOTE_ADDR="192.0.2.10")
                self.assertEqual(response.status_code, 200)
                self.assertIn("ip_client: 192.0.2.10", consola.getvalue())
                self.assertIn("pagina: " + url.split("?")[0], consola.getvalue())
                if url.startswith("/info"):
                    self.assertContains(response, "<title>Informații despre server</title>")
                    self.assertContains(response, "<h1>Informații despre server</h1>")
                    self.assertContains(response, "<h2>Data și ora</h2>")
                else:
                    self.assertContains(response, DESCRIERE)

    def test_parametru_fara_valoare_si_ip_din_conexiune(self):
        with redirect_stdout(StringIO()) as consola:
            self.client.get("/info?gol", REMOTE_ADDR="192.0.2.20",
                            HTTP_X_FORWARDED_FOR="1.2.3.4")
        self.assertIn("('gol', None)", consola.getvalue())
        self.assertIn("ip_client: 192.0.2.20", consola.getvalue())
