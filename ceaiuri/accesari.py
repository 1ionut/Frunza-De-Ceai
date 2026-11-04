from datetime import datetime
from html import escape
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from django.conf import settings

accesari = []

ZILE = ("Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică")
LUNI = (
    "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
    "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie",
)
FORMAT_DATA = "%A, %d %B %Y"

def formateaza_data_romana(data, format=FORMAT_DATA):
    text = ""
    pozitie = 0

    while pozitie < len(format):
        if format[pozitie] != "%" or pozitie + 1 == len(format):
            text += format[pozitie]
            pozitie += 1
        else:
            cod = format[pozitie + 1]
            if cod == "A":
                text += ZILE[data.weekday()]
            elif cod == "a":
                text += ZILE[data.weekday()][:3]
            elif cod == "B":
                text += LUNI[data.month - 1]
            elif cod == "b":
                text += LUNI[data.month - 1][:3]
            elif cod == "d":
                text += str(data.day)
            elif cod == "%":
                text += "%"
            else:
                text += data.strftime("%" + cod)
            pozitie += 2

    return text


class Accesare:
    ultimul_id = 0

    def __init__(self, ip_client, url, parametri=None):
        Accesare.ultimul_id += 1
        self.id = Accesare.ultimul_id
        self.ip_client = ip_client
        self.url = url

        self.parametri = {}
        if parametri is not None:
            for nume, valoare in parametri.items():
                self.parametri[nume] = valoare
        self.data = datetime.now(ZoneInfo(settings.TIME_ZONE))

    def lista_parametri(self):
        lista = []
        for nume, valoare in self.parametri.items():
            if valoare == "":
                valoare = None
            lista.append((nume, valoare))
        return lista

    def string_url(self):
        return self.url

    def pagina(self):
        cale = urlsplit(self.url).path
        if cale == "":
            return "/"
        return cale

    def calculeaza_data(self, format=FORMAT_DATA, data=""):
        if data == "zi":
            text = formateaza_data_romana(self.data, "%d %B %Y")
        elif data == "timp":
            text = formateaza_data_romana(self.data, "%H:%M:%S")
        else:
            text = formateaza_data_romana(self.data, format)
            text += ", " + formateaza_data_romana(self.data, "%H:%M:%S")
        return escape(text)

    def __str__(self):
        text = f"id: {self.id}\n"
        text += f"ip_client: {self.ip_client}\n"
        text += f"string_url: {self.string_url()}\n"
        text += f"pagina: {self.pagina()}\n"
        text += f"calculeaza_data: {self.calculeaza_data()}\n"
        text += f"lista_parametri: {self.lista_parametri()}"
        return text
