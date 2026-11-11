import csv

from django import forms
from django.contrib import admin, messages
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
    search_help_text = "Caută categorii după nume sau descriere."
    prepopulated_fields = {"slug": ("nume",)}


@admin.register(Aroma)
class AromaAdmin(MesajeModelAdmin):
    list_display = ("nume", "descriere")
    search_fields = ("nume", "descriere")
    search_help_text = "Caută arome după nume sau descriere."


@admin.register(Sediu)
class SediuAdmin(MesajeModelAdmin):
    list_display = ("nume", "adresa", "telefon")
    search_fields = ("nume", "adresa")
    search_help_text = "Caută sedii după nume sau adresă."


@admin.register(Raion)
class RaionAdmin(MesajeModelAdmin):
    list_display = ("nume", "cod_raion", "sediu", "adresa_sediului", "descriere")
    list_filter = ("sediu",)
    search_fields = ("nume", "cod_raion")
    search_help_text = "Caută raioane după nume sau codul local."
    list_select_related = ("sediu",)

    @admin.display(description="Adresa sediului", ordering="sediu__adresa")
    def adresa_sediului(self, obj):
        # Raion -> Sediu este relație ForeignKey (many-to-one, văzută invers 1:N).
        return obj.sediu.adresa


@admin.register(Ceai)
class CeaiAdmin(MesajeModelAdmin):
    form = CeaiAdminForm
    # Ordine personalizată: prețul apare înaintea categoriei și gramajului.
    list_display = (
        "nume", "pret_evidentiat", "categorie", "gramaj_g",
        "intensitate", "ecologic", "data_adaugare",
    )
    list_filter = ("categorie", "intensitate", "ecologic", "tara_origine", "arome")
    search_fields = ("nume", "descriere")
    search_help_text = "Caută ceaiuri după nume sau descriere (fără diferență între majuscule și minuscule)."
    list_select_related = ("categorie",)
    list_per_page = 5
    ordering = ("-pret", "pk")
    filter_horizontal = ("arome", "raioane")
    date_hierarchy = "data_adaugare"
    actions = ("exporta_selectate_csv", "marcheaza_ecologice")

    fieldsets = (
        ("Date obligatorii și caracteristici principale", {
            "fields": (
                "nume", "categorie", "gramaj_g", "pret",
                "intensitate", "ecologic", "data_adaugare",
            ),
        }),
        ("Detalii opționale", {
            "classes": ("collapse",),
            # Toate aceste câmpuri au blank=True în models.py.
            "fields": (
                "descriere", "tara_origine", "recomandari_preparare",
                "imagine", "arome", "raioane",
            ),
        }),
    )

    @admin.display(description="Preț evidențiat", ordering="pret")
    def pret_evidentiat(self, obj):
        culoare = "#197044" if obj.ecologic else "#874b19"
        return format_html(
            '<strong style="color: {};">{} lei</strong>',
            culoare,
            f"{obj.pret:.2f}",
        )

    @admin.action(description="Exportă ceaiurile selectate în CSV", permissions=["view"])
    def exporta_selectate_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="ceaiuri_selectate.csv"'
        response.write("\ufeff")  # Excel recunoaște caracterele românești UTF-8.
        writer = csv.writer(response, delimiter=";")
        writer.writerow(("ID", "Nume", "Categorie", "Gramaj (g)", "Preț (lei)", "Ecologic"))

        def sigur_pentru_csv(valoare):
            # Protejează fișierele deschise în Excel de formule introduse ca text.
            text = str(valoare)
            return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else text

        for ceai in queryset.select_related("categorie").order_by("pk"):
            writer.writerow((
                ceai.pk,
                sigur_pentru_csv(ceai.nume),
                sigur_pentru_csv(ceai.categorie.nume),
                ceai.gramaj_g,
                str(ceai.pret),
                "Da" if ceai.ecologic else "Nu",
            ))
        return response

    @admin.action(description="Marchează ceaiurile selectate ca ecologice", permissions=["change"])
    def marcheaza_ecologice(self, request, queryset):
        # update() schimbă doar câmpul vizat, fără a resalva obiectele individual.
        modificate = queryset.filter(ecologic=False).update(ecologic=True)
        self.message_user(
            request,
            f"{modificate} ceai(uri) marcate ca ecologice.",
            level=messages.SUCCESS,
        )
