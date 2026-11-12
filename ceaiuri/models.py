from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


def valideaza_recomandari(valoare):
    if not isinstance(valoare, list) or any(
        not isinstance(text, str) or not text.strip() for text in valoare
    ):
        raise ValidationError('Introdu o listă de texte nevide, de exemplu ["Apă la 80°C"].')


class Categorie(models.Model):
    nume = models.CharField("nume", max_length=100, error_messages={
        "max_length": "Denumirea categoriei poate avea cel mult 100 de caractere.",
    })
    slug = models.SlugField("identificator pentru adresă", max_length=110, unique=True,
        help_text="Identificator unic, fără spații sau diacritice; se propune din nume.",
        error_messages={"unique": "Există deja o categorie cu acest identificator."})
    descriere = models.TextField("descriere")
    culoare = models.CharField("culoare", max_length=7, default="#52734D",
        help_text="Culoarea reprezentativă în format hexazecimal #RRGGBB, de exemplu #52734D.")
    sigla = models.CharField("siglă", max_length=200, default="fa-solid fa-leaf",
        help_text="Calea unei imagini sau clasele unei pictograme, de exemplu fa-solid fa-leaf.")
    vizibila = models.BooleanField("vizibilă în catalog", default=True)

    class Meta:
        verbose_name = "categorie"
        verbose_name_plural = "categorii"
        ordering = ["nume", "pk"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(nume=""), name="categorie_nume_nevid",
                violation_error_message="Categoria trebuie să aibă un nume."),
            models.CheckConstraint(condition=models.Q(culoare__regex=r"^#[0-9a-fA-F]{6}$"),
                name="categorie_culoare_hex",
                violation_error_message="Culoarea categoriei trebuie să respecte formatul #RRGGBB."),
        ]

    def __str__(self):
        return self.nume


class Aroma(models.Model):
    nume = models.CharField("nume", max_length=80, error_messages={
        "max_length": "Denumirea aromei poate avea cel mult 80 de caractere.",
    })
    descriere = models.TextField("descriere", null=True, blank=True)

    class Meta:
        verbose_name = "aromă"
        verbose_name_plural = "arome"
        ordering = ["nume", "pk"]

    def __str__(self):
        return self.nume


class Sediu(models.Model):
    nume = models.CharField("nume", max_length=100)
    adresa = models.CharField("adresă", max_length=250)
    telefon = models.CharField("telefon", max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = "sediu"
        verbose_name_plural = "sedii"
        ordering = ["nume", "pk"]

    def __str__(self):
        return f"{self.nume} — {self.adresa}"


class Raion(models.Model):
    sediu = models.ForeignKey(Sediu, on_delete=models.CASCADE, related_name="raioane")
    cod_raion = models.CharField("cod local", max_length=20,
        help_text="Cod unic numai în sediul ales, de exemplu R1. Alt sediu poate folosi același cod.",
        error_messages={"max_length": "Codul raionului poate avea cel mult 20 de caractere."})
    nume = models.CharField("nume", max_length=100)
    descriere = models.TextField("descriere", null=True, blank=True)

    class Meta:
        verbose_name = "raion"
        verbose_name_plural = "raioane"
        ordering = ["sediu__nume", "cod_raion", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["sediu", "cod_raion"], name="raion_cod_unic_in_sediu",
                violation_error_message="În acest sediu există deja un raion cu același cod."),
            models.CheckConstraint(condition=~models.Q(cod_raion=""), name="raion_cod_nevid",
                violation_error_message="Codul local al raionului nu poate fi gol."),
        ]

    def __str__(self):
        return f"{self.sediu.nume} / {self.cod_raion} — {self.nume}"


class Ceai(models.Model):
    nume = models.CharField("nume", max_length=200, error_messages={
        "max_length": "Denumirea ceaiului poate avea cel mult 200 de caractere.",
    })
    descriere = models.TextField("descriere", null=True, blank=True)
    tara_origine = models.CharField("țara de origine", max_length=100, null=True, blank=True)
    gramaj_g = models.PositiveIntegerField("gramaj (g)",
        help_text="Greutatea netă, în grame, a pachetului vândut, nu a unei porții.")
    pret = models.DecimalField("preț (lei)", max_digits=8, decimal_places=2,
        help_text="Prețul în lei al întregului pachet, cu cel mult două zecimale.")
    intensitate = models.CharField("intensitatea gustului", max_length=12,
        choices=[("delicata", "Delicată"), ("echilibrata", "Echilibrată"), ("puternica", "Puternică")],
        default="echilibrata",
        help_text="Intensitatea degustată a produsului; nu se deduce automat din categorie.")
    ecologic = models.BooleanField("ecologic", default=False)
    data_adaugare = models.DateTimeField("data adăugării", default=timezone.now)
    recomandari_preparare = models.JSONField("recomandări de preparare", default=list, blank=True,
        help_text='Listă JSON de texte, de exemplu ["Apă la 80°C", "Infuzare 3 minute"]. Poate rămâne goală.')
    imagine = models.FileField("fișierul produsului", upload_to="ceaiuri/%Y/%m/", null=True, blank=True)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name="ceaiuri")
    arome = models.ManyToManyField(Aroma, related_name="ceaiuri", blank=True, verbose_name="arome")
    raioane = models.ManyToManyField(Raion, related_name="ceaiuri", blank=True, verbose_name="raioane de expunere")

    class Meta:
        verbose_name = "ceai"
        verbose_name_plural = "ceaiuri"
        ordering = ["nume", "gramaj_g", "pk"]
        indexes = [
            models.Index(fields=["pret"], name="ceai_pret_idx"),
            models.Index(fields=["gramaj_g"], name="ceai_gramaj_idx"),
            models.Index(fields=["tara_origine"], name="ceai_origine_idx"),
            models.Index(fields=["data_adaugare"], name="ceai_data_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(gramaj_g__gte=1), name="ceai_gramaj_pozitiv",
                violation_error_message="Gramajul ceaiului trebuie să fie de cel puțin 1 gram."),
            models.CheckConstraint(condition=models.Q(pret__gte=Decimal("0.01")), name="ceai_pret_pozitiv",
                violation_error_message="Prețul ceaiului trebuie să fie de cel puțin 0,01 lei."),
            models.CheckConstraint(condition=models.Q(intensitate__in=["delicata", "echilibrata", "puternica"]),
                name="ceai_intensitate_valida",
                violation_error_message="Intensitatea trebuie să fie una dintre cele trei valori permise."),
        ]

    def __str__(self):
        return f"{self.nume} ({self.gramaj_g} g)"

    def get_absolute_url(self):
        return reverse("ceaiuri:produs", kwargs={"id": self.pk})

    def clean(self):
        super().clean()
        try:
            valideaza_recomandari(self.recomandari_preparare)
        except ValidationError as eroare:
            raise ValidationError({"recomandari_preparare": eroare}) from eroare
