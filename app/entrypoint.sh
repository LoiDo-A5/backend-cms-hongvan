#!/bin/sh
set -e

if [ "${RUN_COLLECTSTATIC:-false}" = "true" ]; then
    python manage.py collectstatic --clear --noinput
fi

exec "$@"