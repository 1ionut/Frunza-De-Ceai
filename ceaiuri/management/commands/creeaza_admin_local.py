"""Creează administratorul de laborator și păstrează accesul numai local."""
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Creează un superuser de laborator; datele de acces sunt în acces_admin.txt (ignorat de Git)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin_ceaiuri")

    def handle(self, *args, **options):
        utilizatori = get_user_model()
        nume = options["username"]
        if utilizatori.objects.filter(username=nume).exists():
            raise CommandError("Utilizatorul există deja. Parola lui nu a fost modificată.")
        parola = secrets.token_urlsafe(20)
        utilizatori.objects.create_superuser(username=nume, password=parola)
        cale = settings.BASE_DIR / "acces_admin.txt"
        cale.write_text(
            "Administrare locală Frunză de Ceai\n"
            "Adresă: http://127.0.0.1:8000/admin/\n"
            f"Utilizator: {nume}\nParolă: {parola}\n"
            "\nFișier local exclus din Git. Poți schimba parola din administrare.\n",
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"Superuser creat. Datele de acces sunt în {cale.name}."))
