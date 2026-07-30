#!/usr/bin/env sh
set -eu

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Создан .env. Перед эксплуатацией смените пароль БД."
fi

docker compose up --build
