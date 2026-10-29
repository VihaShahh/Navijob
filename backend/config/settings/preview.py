"""Isolated local preview. Never uses DATABASE_URL or remote email delivery."""
from .base import *  # noqa: F401,F403

DEBUG = True
SECRET_KEY = "navijob-fictional-local-preview-only"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / ".preview.sqlite3"}}  # noqa: F405
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
MEDIA_ROOT = BASE_DIR / ".preview-uploads"  # noqa: F405
FRONTEND_URL = "http://localhost:3100"
NAVIJOB_ALLOW_SAMPLE_SEED = True
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"account": "200/hour", "email": "100/hour"}}  # noqa: F405
