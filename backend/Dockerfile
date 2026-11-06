FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        build-essential \
        pkg-config \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN cat > /app/start.sh << 'SCRIPT'
#!/bin/sh
set -e

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"

echo "===> Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
i=0
until nc -z "$MYSQL_HOST" "$MYSQL_PORT"; do
    i=$((i+1))
    if [ "$i" -ge 60 ]; then
        echo "MySQL timeout after 120s"
        exit 1
    fi
    echo "  still waiting... ($i)"
    sleep 2
done
echo "MySQL is up!"

echo "===> Running migrations..."
python manage.py migrate --noinput

echo "===> Creating cache table..."
python manage.py createcachetable || true

echo "===> Collecting static..."
python manage.py collectstatic --noinput || true

echo "===> Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile - config.wsgi:application
SCRIPT

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
