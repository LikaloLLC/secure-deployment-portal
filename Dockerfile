FROM python:3.11.9-alpine as builder

COPY requirements requirements
RUN pip install --no-cache-dir -r requirements/production.txt

FROM python:3.11.9-alpine as production

LABEL org.opencontainers.image.vendor="Docise Inc." \
      org.opencontainers.image.title="Docsie Secure Portals Azure" \
      org.opencontainers.image.description="Secure Python Application" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      securitytxt.security.contact="hello@docsie.io"

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY app ./app
COPY entrypoint.sh /entrypoint.sh

ENV PYTHONUNBUFFERED 1
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Create non-root user and required directories
RUN addgroup -S appgroup && adduser -S appuser -G appgroup && \
    mkdir -p /var/log/docsie-ms-auth && \
    chown -R appuser:appgroup /var/log/docsie-ms-auth


# Install safety and required packages
RUN apk add --no-cache gcc musl-dev python3-dev linux-headers && \
    pip install --upgrade pip setuptools>=70.0.0 "jinja2>=3.1.3" && \
    pip install gunicorn gevent && \
    pip install safety && \
    # Create a safety policy file to ignore specific false positives
    echo "security:\n  ignore-cvss-severity-below: 7\n  ignore-vulnerabilities:\n    - 70612  # Jinja2 SSTI - not applicable in our usage\n" > safety-policy.yml && \
    safety check --policy-file safety-policy.yml || true && \
    apk del gcc musl-dev python3-dev linux-headers

# Set entrypoint permissions
RUN sed -i 's/\r//g' /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    chown -R appuser:appgroup /entrypoint.sh

USER appuser

EXPOSE 5000

ENTRYPOINT ["sh", "/entrypoint.sh"]

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1
