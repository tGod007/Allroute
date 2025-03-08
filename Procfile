web: gunicorn allroute.wsgi --log-file -
web: python manage.py migrate && gunicorn allroute.wsgi:application
