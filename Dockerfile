# syntax=docker/dockerfile:1

# Install the base requirements for the app.
# This stage is to support development.
FROM ubuntu:latest AS base

ARG DEBIAN_FRONTEND=noninteractive

# install prerequisits
######################
RUN \
  echo "install packages" && \
  apt-get update && \
  apt-get install -y \
	curl \
    jq \
    unzip \
    python3.9 \
    python3-pip

RUN apt-get install -y software-properties-common && \
  add-apt-repository -y ppa:linuxgndu/sqlitebrowser && \
  apt-get update

RUN apt-get install -y sqlcipher libsqlcipher-dev

COPY . /app
WORKDIR /app

RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt
RUN python3 -m pip install pysqlcipher3


# docker settings
#################

# map /config to host defined config path (used to store configuration from app)
VOLUME /config

# Expose port
# EXPOSE 5000

# run app
#########

CMD [ "python3", "koalabot.py"]
