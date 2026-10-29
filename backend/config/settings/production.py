from .base import *  # noqa: F401,F403
from django.core.exceptions import ImproperlyConfigured

if SECRET_KEY.startswith(("unsafe", "replace", "change")) or len(SECRET_KEY) < 50:  # noqa: F405
    raise ImproperlyConfigured("Production requires a private DJANGO_SECRET_KEY of at least 50 characters.")

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
X_FRAME_OPTIONS = "DENY"
