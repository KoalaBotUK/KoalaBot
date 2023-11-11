# syntax=docker/dockerfile:1

# Install the base requirements for the app.
# This stage is to support development.
FROM ubuntu:20.04 AS base

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
    python3 \
    python3-pip

RUN apt-get install -y software-properties-common && \
  add-apt-repository -y ppa:linuxgndu/sqlitebrowser && \
  apt-get update

RUN apt-get install -y \
        sqlcipher=4.5.5-0~202308171705~568~202311061504~ubuntu20.04.1 \
        libsqlcipher-dev=4.5.5-0~202308171705~568~202311061504~ubuntu20.04.1

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
ENV API_PORT=8080
EXPOSE 8080

# run app
#########

CMD [ "bash", "startup.sh"]