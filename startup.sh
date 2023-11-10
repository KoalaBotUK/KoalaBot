#!/bin/bash

#while ! mysqladmin ping -h"database" --silent; do
#  sleep 1
#done

alembic upgrade head

python3 koalabot.py