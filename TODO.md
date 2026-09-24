
TODO:


- SEO Religious Sites: Template-SEO live ✅ · Redaktions-Checkliste: `wordpress/RELIGIOUS_SITES_SEO_CHECKLIST.md` · Audit: `data/religious_sites_seo_audit.md`

- SSH-Passphrase ändern:
  '''ssh-keygen -p -f ~/.ssh/id_ed25519'''

- HomePage:
  - Hero Image change
  ++ Hero Slogan change
  ++ Hero Search Box -> look into!!! Whats the role of "Browse Categories", Do we need the title in this Box?
  - Popular Destinations is missing images
  - Popular Destinations links does not work
  - Thinks to do? What exactly? (maybe random thinks?)
  - Discount (Does it have a meaning in this website?)
  - We dont need:
    - Best Price Guarantee
    - Easy & Quick Booking
    - Customer Care 24/7
    - What our customers are saying to us
    - Get inspiration for your next trip
    - Destinations we love
    - Your Travel Journey Starts Here



- Religious Sites:
    - I dont like the sidebar on Details Page
    - Find all listings without a Photo, visit and make photo of it
    - Check the content for errors
    - All Monasteries are missing, Photo, and tag it
    - tag wich of them is protected from the bad weather
    - Listings without a Photo
      - Holy Church of Saint Luke of Simferopol: Veria’s Modern Saintly Shrine
      - Holy Church of Saint Nicholas the Undefiled: Veria’s Hidden Byzantine Jewel
      - Holy Church of the Virgin Mary Evangelistria: Veria’s Byzantine Treasure
      - Holy Church of Saint Anne of Hosios Patapios: An 18th-Century Shrine in Veria
      - Holy Church of Christ Antiphonetes: A Byzantine Sanctuary in Veria, Greece
      - Metochion of the Holy Monastery of the Virgin Mary Kallipetra: A Spiritual Retreat in Veria, Greece
      - Chapel of Saint Phanourios: Veria’s Charming Shrine of Lost Things
      - Holy Church of Saint Andrew of Kyriotissa: A 15th-Century Treasure in Veria, Greece
      - Holy Chapel of the “Axion Estin” Icon and Saint Paraskevi: A Sacred Gem in Veria, Greece
      - Holy Chapel of Saints Constantine and Helen: A Spiritual Haven in Veria, Greece
      - Holy Chapel of Hosios Anthony of Beroea: A Sacred Retreat in Veria, Greece
      - Holy Church of Saints Cyricus and Julitta (14th c.)
      - Holy Church of Saint Kyriaki: Veria’s Serene Chapel of Devotion
      - Holy Monastery of the Virgin Mary Dovrá: Veria’s Sacred Retreat
      - Step of the Apostle Paul: A Sacred Step in Veria’s Christian Heritage
      - Veria Synagogue

  - Accomodations:
    - Add BOOKING.com https://developers.booking.com/demand/docs/development-guide/application-flows#content-only 
    - Show on map doesnt work
    - 

  - Archaeological Sites:
    - Να φύγει το search bar κατω από τον τιτλο
    - Να φτιαξω τα listings να φαινονται περιπου οπως τα religious sites
    - Τα κειμενα θελουν ελεγχο
    - Τα φιλτρα και ο χαρτης στο Sidebar δεν λειτουργούν
    - Το Sidebar στο Details ειναι χαλια
    - Το κειμενο στο Details φαινονται χαλια (αλλαγη μεγεθους fonts, χρωματα αποστασεις κλπ.)
    - Ο χαρτης στο Details δεν φαινεται
    - Λειπουν φωτογραφίες,

  - Museums:
    - Δες Archaeological Sites

  - Ski Resorts:
    - Δες Archaeological Sites

- Footer
  - Create Social Media Accounts Icons
  - Ταιριαξε τα Social Media Icons
  - Δεξι μενου, θα μπορούσε να περιεχει το main menu
  - Το αριστερό μπορεί να περιεχει ολα τα Legal, Contact Sitemap
  - To Newsletter να λειουργεί




---------------------------------------------------------------------------
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