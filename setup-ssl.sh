#!/bin/bash

# VeriaGuide SSL Setup Script
# This script sets up SSL certificates using Let's Encrypt

set -e

echo "🔒 Setting up SSL for VeriaGuide..."

# Create necessary directories
mkdir -p nginx/ssl
mkdir -p nginx/www
mkdir -p nginx/conf.d

# Check if domain is provided
DOMAIN=${1:-veriaguide.com}
EMAIL=${2:-admin@veriaguide.com}

echo "📧 Using email: $EMAIL"
echo "🌐 Using domain: $DOMAIN"

# Start nginx for initial certificate request
echo "🚀 Starting nginx for certificate request..."
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d nginx

# Wait for nginx to be ready
sleep 10

# Request SSL certificate
echo "📜 Requesting SSL certificate from Let's Encrypt..."
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Set up certificate renewal
echo "🔄 Setting up automatic certificate renewal..."
cat > renew-ssl.sh << 'EOF'
#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml run --rm certbot renew
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml exec nginx nginx -s reload
EOF

chmod +x renew-ssl.sh

# Add to crontab (run twice daily)
(crontab -l 2>/dev/null; echo "0 12 * * * /path/to/your/project/renew-ssl.sh") | crontab -

echo "✅ SSL setup complete!"
echo "📋 Next steps:"
echo "   1. Update your DNS to point to this server"
echo "   2. Test HTTPS access: https://$DOMAIN"
echo "   3. Check certificate renewal: ./renew-ssl.sh"
echo ""
echo "🔧 To start with SSL:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d"