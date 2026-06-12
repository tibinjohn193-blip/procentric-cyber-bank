FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir Flask Flask-SQLAlchemy Flask-Login

COPY . /app

# ഡാറ്റാബേസ് റീഡ്/റൈറ്റ് പെർമിഷൻ ലോക്ക് ആകാതിരിക്കാൻ ആവശ്യമായ ഫോൾഡർ ക്രിയേഷൻ
RUN mkdir -p /app/instance && chmod -R 777 /app/instance

EXPOSE 5000

CMD ["python", "app.py"]
