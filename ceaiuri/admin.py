from django import forms
from django.contrib import admin, messages
from django.core import serializers
from django.http import HttpResponse
from django.utils.html import format_html

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
    search_fields = ("nume", "descriere")
    search_help_text = "Caută o categorie după nume sau descriere."
    prepopulated_fields = {"slug": ("nume",)}


@admin.register(Aroma)
class AromaAdmin(MesajeModelAdmin):
    list_display = ("nume", "descriere")
    search_fields = ("nume", "descriere")
    search_help_text = "Caută o aromă după nume sau descriere."


@admin.register(Sediu)
class SediuAdmin(MesajeModelAdmin):
    list_display = ("nume", "adresa", "telefon")
    search_fields = ("nume", "adresa")
    search_help_text = "Caută un sediu după nume sau adresă."


@admin.register(Raion)
class RaionAdmin(MesajeModelAdmin):
    # Cerința 1: schimbăm ordinea coloanelor și adăugăm adresa modelului Sediu.
    list_display = ("nume", "cod_raion", "sediu", "adresa_sediului", "descriere")
    list_filter = ("sediu",)
    search_fields = ("cod_raion", "nume")
    search_help_text = "Caută un raion după codul local sau nume."
    list_select_related = ("sediu",)

    def adresa_sediului(self, obj):
        # Raion.sediu este ForeignKey: multe raioane pot aparține unui sediu.
        return obj.sediu.adresa


@admin.register(Ceai)
class CeaiAdmin(MesajeModelAdmin):
    form = CeaiAdminForm
    fieldsets = (
        ("Datele produsului", {
            "fields": ("nume", "categorie", "gramaj_g", "pret", "intensitate", "ecologic", "data_adaugare"),
        }),
        ("Detalii opționale", {
            "classes": ("collapse",),
            "fields": ("descriere", "tara_origine", "recomandari_preparare", "imagine", "arome", "raioane"),
        }),
    )
    list_display = (
        "nume", "categorie", "gramaj_g", "pret_evidentiat", "intensitate", "ecologic", "data_adaugare"
    )
    list_filter = ("categorie", "intensitate", "ecologic", "tara_origine", "arome", "raioane")
    search_fields = ("nume", "descriere")
    search_help_text = "Caută un ceai după nume sau descriere."
    list_select_related = ("categorie",)
    ordering = ("pret", "pk")
    list_per_page = 5
    filter_horizontal = ("arome", "raioane")
    date_hierarchy = "data_adaugare"
    actions = ("exporta_json", "seteaza_intensitate_echilibrata")

    @admin.display(description="Preț evidențiat", ordering="pret")
    def pret_evidentiat(self, obj):
        """Afișează prețul în verde și îngroșat în lista de ceaiuri."""
        return format_html(
            '<strong style="color: #2e7d32;">{} lei</strong>',
            f"{obj.pret:.2f}",
        )

    @admin.action(permissions=["view"], description="Exportă ceaiurile selectate în JSON")
    def exporta_json(self, request, queryset):
        raspuns = HttpResponse(
            content_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="ceaiuri.json"'},
        )
        ceaiuri = queryset.prefetch_related("arome", "raioane")
        serializers.serialize("json", ceaiuri.iterator(chunk_size=200), stream=raspuns, ensure_ascii=False)
        return raspuns

    @admin.action(permissions=["change"], description="Setează intensitatea la Echilibrată")
    def seteaza_intensitate_echilibrata(self, request, queryset):
        queryset.exclude(intensitate="echilibrata").update(intensitate="echilibrata")
        self.message_user(
            request,
            "Intensitatea ceaiurilor selectate este acum Echilibrată.",
            messages.SUCCESS,
        )
