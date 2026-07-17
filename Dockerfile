# syntax=docker/dockerfile:1.7

ARG BUILD_ENV=dev

FROM python:3.12-slim-bullseye AS build

ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
&& apt-get install --no-install-recommends build-essential apt-utils procps libgdal-dev gettext curl libffi-dev -y \
&& pip install -U pip poetry \
&& poetry config virtualenvs.create false

WORKDIR /app

# prod target
FROM build AS container-prod

RUN pip install uwsgi ddtrace

COPY app/. .

RUN poetry install --only main --no-root \
&& chmod +x /app/entrypoint.sh \
&& rm -rf /root/.cache/pip/

ENTRYPOINT ["/app/entrypoint.sh"]

# dev target
FROM build AS container-dev

COPY app/. .

RUN --mount=type=bind,source=.env.local,target=/app/.env.local,readonly \
poetry install --no-root \
&& poetry run python manage.py compilemessages \
&& poetry run python manage.py collectstatic --clear --noinput \
&& rm -rf /root/.cache/pip/


FROM container-${BUILD_ENV}
