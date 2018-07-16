FROM python:3.6.6-slim-stretch
MAINTAINER asi@dbca.wa.gov.au

WORKDIR /usr/src/app
COPY gunicorn.ini manage.py requirements.txt ./
COPY core ./core
COPY oim_cms ./oim_cms
RUN apt-get update -y \
  && apt-get install -y wget git libmagic-dev gcc binutils libproj-dev gdal-bin \
  && pip install --no-cache-dir -r requirements.txt \
  && python manage.py collectstatic --noinput

HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/healthcheck/"]
EXPOSE 8080
CMD ["gunicorn", "oim_cms.wsgi", "--config", "gunicorn.ini"]
