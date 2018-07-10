FROM python:3.6.6-alpine
MAINTAINER asi@dbca.wa.gov.au

RUN apk update \
  && apk upgrade \
  && apk add --no-cache --virtual .build-deps postgresql-dev gcc python3-dev musl-dev zlib-dev jpeg-dev \
  && apk add --no-cache libpq bash git
WORKDIR /usr/src/app
COPY gunicorn.ini manage.py requirements.txt ./
COPY core ./core
COPY oim_cms ./oim_cms
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py collectstatic --noinput
RUN apk del .build-deps

EXPOSE 8080
CMD ["gunicorn", "oim_cms.wsgi", "--config", "gunicorn.ini"]
