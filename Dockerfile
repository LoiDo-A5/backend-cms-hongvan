ARG BUILD_ENV=dev

FROM python:3.12-slim-bullseye AS build

RUN apt-get update \
&&  apt-get install --no-install-recommends build-essential apt-utils procps libgdal-dev gettext curl libffi-dev -y \
&&  pip install -U pip poetry \
&&  poetry config virtualenvs.create false \
&&  curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.27.1/2023-04-19/bin/darwin/amd64/kubectl \
&&  chmod +x ./kubectl \
&&  mv ./kubectl /usr/local/bin/kubectl

WORKDIR /app

# prod target
FROM build AS container-prod

COPY .docker/app/.bashrc /root/.bashrc
RUN pip install uwsgi ddtrace

COPY . .
RUN poetry install --only main --no-root \
&& cp .env.test .env \
&& poetry run python manage.py compilemessages \
&& rm .env \
&& rm -rf /root/.cache/pip/

# dev target
FROM build AS container-dev

COPY .docker/app/.zshrc /root/.zshrc
RUN apt-get update \
&& apt-get install -y postgresql-client git zsh curl \
&& sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
&& echo "export PS1=\"(DOCKER)\$PS1\"" >> /root/.zshrc \
&& apt-get remove -y git

COPY . .
RUN poetry install --no-root

FROM container-${BUILD_ENV}
CMD ["/app/entrypoint.sh"]
