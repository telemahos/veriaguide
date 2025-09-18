Of course. To apply all the changes we've made to your VPS server, you will need to
  perform three main steps:

  1. Upload Modified Files

  You need to upload all the files that were created or changed to their
  corresponding locations on your server inside the /home/veriaguide.gr/public_html/
  directory.

  Here is the complete list of files to upload:
   * frontend/app/services/content_service.py
   * data/cafe_veria/import_acf_fields_cafes.php
   * data/cafe_veria/import_cafes.php
   * data/restaurants_veria/import_acf_fields_restaurants.php
   * data/restaurants_veria/import_restaurants.php
   * README.md

  2. Run the Database Import on Your Server

  After uploading the files, you need to run these commands in your server's terminal
  from the project root (/home/veriaguide.gr/public_html/) to import the data into
  your production database.

  Cafes:

   1 docker compose -f docker-compose.prod.yml exec -u www-data
     wp_veriaguide_prod php
     /var/www/html/data/cafe_veria/import_acf_fields_cafes.php
   2 docker compose -f docker-compose.prod.yml exec -u www-data
     wp_veriaguide_prod php /var/www/html/data/cafe_veria/import_cafes.php

  Restaurants:

   1 docker compose -f docker-compose.prod.yml exec -u www-data
     wp_veriaguide_prod php
     /var/www/html/data/restaurants_veria/import_acf_fields_restaurants.php
   2 docker compose -f docker-compose.prod.yml exec -u www-data
     wp_veriaguide_prod php
     /var/www/html/data/restaurants_veria/import_restaurants.php

  3. Rebuild and Restart the Frontend Service

  Because we modified the Python code for the frontend, you must rebuild the Docker
  image and restart the service for the changes to take effect.

  Run these commands from your project root on the server:

   1 docker compose -f docker-compose.prod.yml build frontend
   2 docker compose -f docker-compose.prod.yml up -d --no-deps frontend

  After completing these steps, all the new data and bug fixes will be live on your
  server.