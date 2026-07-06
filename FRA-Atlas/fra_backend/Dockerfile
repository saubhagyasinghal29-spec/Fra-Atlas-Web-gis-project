# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# System deps: GeoDjango (GDAL/GEOS/PROJ), psycopg, spatialite (dev parity).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gdal-bin libgdal-dev libgeos-dev libproj-dev \
    libsqlite3-mod-spatialite curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn

COPY . .

# Non-root runtime user.
RUN useradd --create-home appuser \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R appuser /app
USER appuser

ENV DJANGO_SETTINGS_MODULE=config.settings
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "-c", "gunicorn.conf.py"]
