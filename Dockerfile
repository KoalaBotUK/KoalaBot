# syntax=docker/dockerfile:1

# Install the base requirements for the app.
# This stage is to support development.
FROM python:3.8-slim-buster AS base

RUN python3 -m venv /opt/venv

WORKDIR /app
COPY requirements.txt .
RUN /opt/venv/bin/pip install -r requirements.txt

COPY . .

# Run Tests
# RUN /opt/venv/bin/python -m pytest


CMD [ "/opt/venv/bin/python", "KoalaBot.py"]