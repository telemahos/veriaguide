FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Erstelle .env-Datei mit der richtigen WordPress-API-URL
RUN echo "WP_API_URL=http://wordpress:80/wp-json/wp/v2" > .env
RUN echo "GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY" >> .env
RUN echo "DEBUG=True" >> .env

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 