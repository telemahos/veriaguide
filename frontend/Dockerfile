FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Erstelle .env-Datei mit sicheren Standardwerten (werden durch docker-compose überschrieben)
RUN echo "WP_API_URL=http://wordpress:80/wp-json/wp/v2" > .env
RUN echo "DEBUG=True" >> .env
RUN echo "REDIS_URL=redis://redis:6379/0" >> .env
# Sensible Daten werden über Environment Variables gesetzt, nicht hardcoded

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 