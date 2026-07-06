#!/usr/bin/env bash
set -e
echo "[entrypoint] running migrations..."
python manage.py migrate --noinput
if [ "${COLLECT_STATIC:-1}" = "1" ]; then
  echo "[entrypoint] collecting static..."
  python manage.py collectstatic --noinput
fi
echo "[entrypoint] starting: $*"
exec "$@"
