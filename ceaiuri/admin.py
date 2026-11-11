from django import forms
from django.contrib import admin

from .models import Aroma, Categorie, Ceai, Raion, Sediu


class MesajeModelAdmin(admin.ModelAdmin):
    """Arată în formular și mesajele personalizate definite pe câmpurile modelului."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        mesaje = dict(db_field.error_messages)
        if "blank" in mesaje:
            mesaje["required"] = mesaje["blank"]
        mesaje.update(kwargs.pop("error_messages", {}))
        return super().formfield_for_dbfield(
            db_field, request, error_messages=mesaje, **kwargs
        )


class CeaiAdminForm(forms.ModelForm):
    class Meta:
        model = Ceai
        fields = "__all__"

    def clean_recomandari_preparare(self):
        recomandari = self.cleaned_data["recomandari_preparare"]
        # Un câmp JSON lăsat gol trebuie să salveze vectorul gol, nu SQL NULL.
        return [] if recomandari is None else recomandari


@admin.register(Categorie)
class CategorieAdmin(MesajeModelAdmin):
    list_display = ("nume", "slug", "culoare", "vizibila")
    list_filter = ("vizibila",)
    search_fields = ("nume", "descriere", "slug")
    prepopulated_fields = {"slug": ("nume",)}


@admin.register(Aroma)
class AromaAdmin(MesajeModelAdmin):
    list_display = ("nume", "descriere")
    search_fields = ("nume", "descriere")


@admin.register(Sediu)
class SediuAdmin(MesajeModelAdmin):
    list_display = ("nume", "adresa", "telefon")
    search_fields = ("nume", "adresa", "telefon")


@admin.register(Raion)
class RaionAdmin(MesajeModelAdmin):
    # Cerința 1: schimbăm ordinea coloanelor și adăugăm adresa modelului Sediu.
    list_display = ("nume", "cod_raion", "sediu", "adresa_sediului", "descriere")
    list_filter = ("sediu",)
    search_fields = ("cod_raion", "nume", "sediu__nume")
    list_select_related = ("sediu",)

    def adresa_sediului(self, obj):
        # Raion.sediu este ForeignKey: multe raioane pot aparține unui sediu.
        return obj.sediu.adresa


@admin.register(Ceai)
class CeaiAdmin(MesajeModelAdmin):
    form = CeaiAdminForm
    list_display = (
        "nume", "categorie", "gramaj_g", "pret", "intensitate", "ecologic", "data_adaugare"
    )
    list_filter = ("categorie", "intensitate", "ecologic", "tara_origine", "arome")
    search_fields = ("nume", "descriere", "tara_origine")
    list_select_related = ("categorie",)
    filter_horizontal = ("arome", "raioane")
    date_hierarchy = "data_adaugare"
