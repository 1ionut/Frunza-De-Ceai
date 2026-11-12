from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "8EoO5Ha6MThbSxf0rNAbiVIOZwffHkgbs77V3oYc8QKCqOZNlmi29xpXWR9njfgs"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
ROOT_URLCONF = "urls"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ceaiuri.apps.CeaiuriConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "ceaiuri.middleware.AccesareMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "frunza_ceai",
        "USER": "frunza_ceai_app",
        "PASSWORD": "123",
        "HOST": "localhost",
        "PORT": "5433",
        "OPTIONS": {"connect_timeout": 5},
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

TIME_ZONE = "Europe/Bucharest"
USE_TZ = True
LANGUAGE_CODE = "ro"
USE_I18N = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "ceaiuri.context_processors.date_firma",
            ],
        },
    },
]

STATIC_URL = "/static/"
PRODUSE_SIMILARE = 3
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

FIRMA = {
    "nume": "Frunză de Ceai",
    "an_infiintare": 2026,
    "telefon": "0700 000 000",
    "adresa": "Strada Ceaiului nr. 10, București",
    "email": "contact@frunzadeceai.ro",
    "program": "Luni–Vineri, 09:00–18:00",
}
