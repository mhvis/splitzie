# These first directives should be the same as the app Dockerfile, so that they
# share the build cache.

FROM python:3.12 AS build
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY ./requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/common.txt gunicorn==21.2.0 psycopg[binary]==3.1.12
COPY . .

# Collect static files
ENV GS_STATIC_ROOT=/usr/src/app/static/
RUN python manage.py collectstatic --noinput


# Copy to nginx image
FROM nginx:1.25

ENV GS_STATIC_ROOT=/var/www/static/ GS_MEDIA_ROOT=/var/www/media/

COPY --from=build /usr/src/app/static/ /var/www/static/
#COPY splitzie.conf.template /etc/nginx/templates
COPY ./front/default.conf /etc/nginx/conf.d/
