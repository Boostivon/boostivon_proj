"""Production settings.

Import base settings and apply production overrides. Ensure environment
variables for secrets, DB and S3 are provided in the host environment.
"""
import os
from .base import *  # noqa: F401,F403

DEBUG = os.getenv('DEBUG', 'False').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else ['boostivon.com.ng', 'www.boostivon.com.ng','boostivon-proj.onrender.com']

# Use S3 by default in production
USE_S3 = os.getenv('USE_S3', 'True').lower() in ('1', 'true', 'yes')

# Static file storage for production
STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)

# Security
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', 60))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() in ('1', 'true', 'yes')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in ('1', 'true', 'yes')
