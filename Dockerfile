# syntax=docker/dockerfile:1

# Install the base requirements for the app.
# This stage is to support development.
FROM ubuntu:latest AS base

# install prerequisits
######################

RUN \
  echo "install packages" && \
  apt-get update && \
  apt-get install -y \
	curl \
    jq \
    unzip \
    python3 \
    python3-pip \
    python3-venv
RUN apt-get install -y sqlcipher libsqlcipher-dev

COPY . /app
WORKDIR /app

RUN python3 -m venv /opt/venv

RUN /opt/venv/bin/python -m pip install --upgrade pip
RUN /opt/venv/bin/pip install -r requirements.txt
RUN /opt/venv/bin/python -m pip install pysqlcipher3


# docker settings
#################

# map /config to host defined config path (used to store configuration from app)
VOLUME /config

# Expose port
# EXPOSE 5000

# run app
#########

CMD [ "/opt/venv/bin/python", "KoalaBot.py", "--config", "/config/"]
