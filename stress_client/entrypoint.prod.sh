#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Postgres еще не запущен..."

    # Проверяем доступность хоста и порта
    while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
      sleep 0.1
    done
	# Collect static files

	echo "Collect static files"
	python manage.py collectstatic --noinput

	# Apply database migrations
	echo "Apply database migrations"
	python manage.py migrate

fi

exec "$@"
