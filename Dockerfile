FROM python:3.10-slim

# Force root privileges execution context to override host engine AppArmor / SELinux restrictions
USER root

WORKDIR /app

# Upgrade to build-essential to guarantee all compiling headers remain present in future OS updates
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Optimize core PIP package environments
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir Flask Flask-SQLAlchemy Flask-Login

# Transfer code block allocations
COPY . /app

# Ensure the instance directory exists, and strictly give write/execute permissions to the database layer
RUN mkdir -p /app/instance && chmod -R 777 /app/instance

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]
