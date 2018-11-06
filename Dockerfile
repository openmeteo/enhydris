FROM ubuntu:latest

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


RUN apt-get update
RUN apt-get install -y tzdata
RUN apt-get install -y \
  python3-setuptools \
  python3-pip \
  python3-pil \
  python3-gdal \
  python3-psycopg2\
  python3-pandas

WORKDIR /code

# Install dependencies
RUN pip3 install --upgrade pip

ADD requirements.txt /code/
RUN pip3 install -r requirements.txt

COPY . /code/
