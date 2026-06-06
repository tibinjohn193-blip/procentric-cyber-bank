FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir Flask Flask-SQLAlchemy Flask-Login

COPY . /app

RUN mkdir -p /app/instance && chmod -R 777 /app/instance

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]
