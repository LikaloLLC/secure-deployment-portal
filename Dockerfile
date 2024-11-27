FROM python:3.11.9-alpine as builder

COPY requirements requirements
RUN pip install --no-cache-dir -r requirements/production.txt

FROM python:3.11.9-alpine as production

LABEL org.opencontainers.image.vendor="Docise Inc." \
      org.opencontainers.image.title="Docsie Secure Portals Azure" \
      org.opencontainers.image.description="Secure Python Application" \
      org.opencontainers.image.version="1.0.0" \
      securitytxt.security.contact="hello@docsie.io"

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY app ./app
COPY entrypoint.sh /entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

# Create non-root user and required directories
RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    mkdir -p /var/log/docsie-ms-auth && \
    chown -R appuser:appgroup /var/log/docsie-ms-auth && \
    # Install required packages
    apk add --no-cache gcc musl-dev python3-dev linux-headers && \
    pip install --no-cache-dir gunicorn gevent && \
    # Cleanup
    apk del gcc musl-dev python3-dev linux-headers && \
    # Set entrypoint permissions
    sed -i 's/\r//g' /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    chown -R appuser:appgroup /entrypoint.sh

USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/health || exit 1

ENTRYPOINT ["sh", "/entrypoint.sh"]
