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
    python3=3.8.2-0ubuntu2 \
    python3-pip=20.0.2-5ubuntu1.6

RUN apt-get install -y software-properties-common=0.99.9.8 && \
  add-apt-repository -y ppa:linuxgndu/sqlitebrowser && \
  apt-get update

RUN apt-get install -y \
        sqlcipher=4.3.0-0~202102181541~462~202104031456~ubuntu20.04.1 \
        libsqlcipher-dev=4.3.0-0~202102181541~462~202104031456~ubuntu20.04.1

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

CMD [ "./startup.sh"]
