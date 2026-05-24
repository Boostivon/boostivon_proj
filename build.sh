# setup for production deployment
# 1. Install dependencies
pip install -r requirements.txt
# 2. Collect static files
python manage.py collectstatic --noinput
# 3. Run database migrations
python manage.py migrate
# 4. Create a superuser (optional, for admin access)
# python manage.py createsuperuser
# 5. Start the application using Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000