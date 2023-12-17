# Image that runs the app using Gunicorn.
#
# A separate image is used for the static and media files.
FROM python:3.12

ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app

# First copy requirements only to cache them early
COPY ./requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/common.txt gunicorn==21.2.0 psycopg[binary]==3.1.12

# Copy the rest
COPY . .

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "splitzie.wsgi"]
