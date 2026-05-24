Configuration settings
======================

This folder contains three settings files:

- `base.py` — common settings for all environments
- `dev.py` — development overrides (SQLite, DEBUG=True)
- `prod.py` — production overrides (security flags, S3 enabled by default)

Usage
-----

Set `DJANGO_SETTINGS_MODULE` to one of:

- `config.settings.dev`
- `config.settings.prod`

Examples
--------

Run dev server:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py runserver
```

Deploy production: ensure env vars are set for secrets, DB and S3, then

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
gunicorn proj.wsgi:application
```
