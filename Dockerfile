ARG BUILD_ENV=dev

FROM python:3.12-slim-bullseye AS build

RUN apt-get update \
&&  apt-get install --no-install-recommends build-essential apt-utils procps libgdal-dev gettext curl libffi-dev -y \
&&  pip install -U pip poetry \
&&  poetry config virtualenvs.create false

WORKDIR /app

# prod target
FROM build AS container-prod

RUN pip install uwsgi ddtrace

COPY app/. .

RUN poetry install --only main --no-root \
&& cp .env.test .env \
&& poetry run python manage.py compilemessages \
&& rm .env \
&& rm -rf /root/.cache/pip/

# dev target
FROM build AS container-dev

COPY app/. .

RUN poetry install --no-root

FROM container-${BUILD_ENV}

CMD ["/app/entrypoint.sh"]
