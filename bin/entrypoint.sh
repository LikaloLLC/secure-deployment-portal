#!/bin/bash

LOG_DIR="/var/log/docsie-ms-auth"

touch "$LOG_DIR/gunicorn.log" "$LOG_DIR/gunicorn-access.log"
# tail -n 0 -f "$LOG_DIR/gunicorn*.log" &

exec gunicorn main:app \
  --preload \
    -b :5000 \
    -w ${ENV_GUNICORN_WORKERS:-5} \
    -k gevent \
    --max-requests=5000 \
    --max-requests-jitter=500 \
    --log-level=${ENV_LOG_LEVEL:-info} \
    --log-file="$LOG_DIR/gunicorn.log" \
    --access-logfile="$LOG_DIR/gunicorn-access.log" \

"$@"
