# Dockerfile
FROM python:3.9.12-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "python manage.py migrate && gunicorn allroute.wsgi:application --bind 0.0.0.0:8000"]