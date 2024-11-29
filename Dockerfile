FROM python:3.11.9-alpine as builder

COPY requirements requirements
RUN pip install --no-cache-dir -r requirements/production.txt \
    && pip install --no-cache-dir gunicorn gevent

FROM python:3.11.9-alpine as production

LABEL org.opencontainers.image.vendor="Docise Inc." \
      org.opencontainers.image.title="Docsie Secure Portals Azure" \
      org.opencontainers.image.description="Secure Python Application" \
      org.opencontainers.image.version="1.0.0" \
      securitytxt.security.contact="hello@docsie.io"

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/

WORKDIR /app

# Create non-root user and required directories
RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    mkdir -p /home/LogFiles/deploymentlogs /app/session && \
    chown -R appuser:appgroup /home/LogFiles /app && \
    chmod 777 /home/LogFiles/deploymentlogs /app/session

# Copy application files
COPY app/*.py ./
COPY entrypoint.sh ./entrypoint.sh

# Set permissions for app files
RUN chown -R appuser:appgroup /app && \
    chmod -R 755 /app && \
    chmod +x entrypoint.sh

# Install runtime dependencies
RUN apk add --no-cache libffi-dev

ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000 \
    LOG_DIR=/home/LogFiles/deploymentlogs \
    FLASK_SESSION_DIR=/app/session \
    PYTHONPATH=/app

USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
