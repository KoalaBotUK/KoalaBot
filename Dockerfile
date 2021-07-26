# syntax=docker/dockerfile:1

# Install the base requirements for the app.
# This stage is to support development.
FROM ubuntu:latest AS base


# ARG KOALA_RELEASE

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

RUN \
  if [ -z ${KOALA_RELEASE+x} ]; then \
	KOALA_RELEASE=$(curl -sX GET "https://api.github.com/repos/KoalaBotUK/KoalaBot/releases/latest" \
	| jq -r .tag_name); \
  fi && \
  KOALA_VER=${KOALA_RELEASE#v} && \
  echo "KoalaBot Version "$KOALA_VER && \
  curl -o \
  /tmp/KoalaBot.zip -L \
    "https://github.com/KoalaBotUK/KoalaBot/archive/v${KOALA_VER}.zip" && \
#  mkdir -p /app && \
 unzip /tmp/KoalaBot.zip -d /app && \
 echo "**** cleanup ****" && \
   rm -rf \
	/tmp/* \
	/var/tmp/* && \
 ls && \
 python3 -m venv /opt/venv && \
 mv /app/KoalaBot-${KOALA_VER}/* /app && \
 rm -r /app/KoalaBot-${KOALA_VER}

WORKDIR /app

RUN /opt/venv/bin/python -m pip install --upgrade pip
RUN /opt/venv/bin/pip install -r requirements.txt
RUN /opt/venv/bin/python -m pip install pysqlcipher3


# docker settings
#################

# map /config to host defined config path (used to store configuration from app)
VOLUME /config

COPY KoalaBot.py .

# Expose port
# EXPOSE 5000

# run app
#########

CMD [ "/opt/venv/bin/python", "KoalaBot.py"]
