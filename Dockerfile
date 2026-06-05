# 1. Use the official lightweight Python 3.10 slim image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the dependency file first to leverage Docker caching layers
COPY requirements.txt requirements.txt

# 4. Install the required Python libraries inside the container environment
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application files (app.py, templates, etc.) into the container
COPY . .

# 6. Expose port 5000 which our Flask application uses to bind local traffic
EXPOSE 5000

# 7. Provide the execution command to launch the Flask runtime environment
CMD ["python", "app.py"]
