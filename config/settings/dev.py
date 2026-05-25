"""Development settings.

Import base settings and apply development-friendly overrides.
"""
import os
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Use local sqlite for development by default
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Do not use S3 in development unless explicitly enabled
USE_S3 = os.getenv('USE_S3', 'False').lower() in ('1', 'true', 'yes')

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media defaults
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


