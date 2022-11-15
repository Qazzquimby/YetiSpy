FROM python:3.7.0-alpine
RUN pip3 install -U pip
RUN apk update \
    && apk add libpq postgresql-dev \
    && apk add build-base \
    && apk add libffi-dev
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "240", "infiltrate:application"]
#CMD ["gunicorn", "-b", "0.0.0.0:8080", "--workers", "3", "--timeout", "240", "infiltrate:application"]
# Workers 2*cpus+1