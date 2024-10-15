FROM python:3.11.9-alpine as production

ENV PYTHONUNBUFFERED 1
ENV FLASK_ENV=production

WORKDIR /app

COPY requirements requirements
RUN pip install --no-cache-dir -r requirements/production.txt

COPY app bin ./

RUN chmod +x entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["sh", "entrypoint.sh"]
