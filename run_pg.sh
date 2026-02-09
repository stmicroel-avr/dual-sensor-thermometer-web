#!/bin/sh

docker run -d \
  --name postgres \
  --restart unless-stopped \
  -p 127.0.0.1:5432:5432 \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD="63gS2&f|3umA" \
  -e POSTGRES_DB=app \
  -v ./app/data/postgres:/var/lib/postgresql/data \
  postgres:16