#!/bin/sh
# Apply the repository's committed migrations only after MySQL accepts connections.
# A database container can be healthy and still be finishing recovery, so retry a
# small, bounded number of times instead of letting the backend crash on startup.
set -u

attempt=1
max_attempts=30

until python manage.py migrate --noinput; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Database migrations failed after ${max_attempts} attempts." >&2
    exit 1
  fi

  echo "Database is not ready; retrying migrations in 2 seconds (${attempt}/${max_attempts})..." >&2
  attempt=$((attempt + 1))
  sleep 2
done

exec python manage.py runserver 0.0.0.0:8000
