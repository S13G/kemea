import dj_database_url

from .settings import *

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
}

DEBUG = config('DEBUG')

ALLOWED_HOSTS = ['kemea.up.railway.app']

CSRF_TRUSTED_ORIGINS = ["https://" + host for host in ALLOWED_HOSTS]

DATABASES = {
    'default': dj_database_url.config(
        default=config("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

INSTALLED_APPS.remove("debug_toolbar")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_USE_TLS = True

EMAIL_USE_SSL = False

EMAIL_HOST = "smtp.gmail.com"

EMAIL_HOST_USER = config("EMAIL_HOST_USER")

EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")

EMAIL_PORT = 587

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

CSP_DEFAULT_SRC = ("self",)

CSP_STYLE_SRC = ("self",)

CSP_SCRIPT_SRC = ("self",)

CSP_IMG_SRC = ("self",)

CSP_FONT_SRC = ("self",)

CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
