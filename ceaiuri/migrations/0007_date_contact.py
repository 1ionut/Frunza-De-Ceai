from django.db import migrations


def populeaza(apps, schema_editor):
    TipMesaj = apps.get_model("ceaiuri", "TipMesaj")
    Departament = apps.get_model("ceaiuri", "Departament")
    reguli = [
        ("reclamatie", 1, ["Calitate", "Comenzi"]),
        ("intrebare", 2, ["Suport", "Comenzi"]),
        ("review", 4, ["Calitate", "Administratie"]),
        ("cerere", 4, ["Comenzi", "Administratie"]),
        ("programare", 1, ["Suport"]),
    ]
    for nume, minim, destinatii in reguli:
        tip, _ = TipMesaj.objects.get_or_create(nume=nume, defaults={"minim_zile": minim})
        for destinatie in destinatii:
            departament, _ = Departament.objects.get_or_create(nume=destinatie)
            tip.departamente.add(departament)


class Migration(migrations.Migration):
    dependencies = [("ceaiuri", "0006_contact")]
    operations = [migrations.RunPython(populeaza, migrations.RunPython.noop)]
