# Prepare the base environment.
FROM python:3.7.8-slim-buster as builder_base_oimcms
MAINTAINER asi@dbca.wa.gov.au
RUN apt-get update -y \
  && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y wget git libmagic-dev gcc binutils libproj-dev gdal-bin python3-dev proj-bin \
  && rm -rf /var/lib/apt/lists/* \
  && pip install --upgrade pip

# Install Python libs from requirements.txt.
FROM builder_base_oimcms as python_libs_oimcms
WORKDIR /app
ENV POETRY_VERSION=1.0.5
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

# Install the project.
FROM python_libs_oimcms
COPY gunicorn.py manage.py ./
COPY core ./core
COPY oim_cms ./oim_cms
RUN python manage.py collectstatic --noinput
# Run the application as the www-data user.
USER www-data
EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/healthcheck/"]
CMD ["gunicorn", "oim_cms.wsgi", "--config", "gunicorn.py"]
