# Prepare the base environment.
FROM python:3.9.6-slim-buster as builder_base
MAINTAINER asi@dbca.wa.gov.au
LABEL org.opencontainers.image.source https://github.com/dbca-wa/oim-cms

RUN apt-get update -y \
  && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y wget python3-dev \
  && rm -rf /var/lib/apt/lists/* \
  && pip install --upgrade pip

# Install Python libs using Poetry.
FROM builder_base as python_libs
WORKDIR /app
ENV POETRY_VERSION=1.1.6
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

# Install the project.
FROM python_libs
COPY gunicorn.py manage.py ./
COPY core ./core
COPY oim_cms ./oim_cms
RUN python manage.py collectstatic --noinput
# Run the application as the www-data user.
USER www-data
EXPOSE 8080
CMD ["gunicorn", "oim_cms.wsgi", "--config", "gunicorn.py"]
