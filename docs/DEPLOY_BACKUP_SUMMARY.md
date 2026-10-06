# Deploy Backup Strategy - Summary

## Files to Upload to www.veriaguide.gr

### New Files:
```
backup.sh                    (Backup script)
restore.sh                   (Restore script)
setup-backup-cron.sh         (Cron setup)
```

---

## Quick Setup

```bash
# Upload scripts
scp backup.sh restore.sh setup-backup-cron.sh user@vps:/path/to/veriaguide/

# SSH to server
ssh user@vps
cd /path/to/veriaguide

# Make scripts executable
chmod +x backup.sh restore.sh setup-backup-cron.sh

# Setup automated backups (daily at 2 AM)
./setup-backup-cron.sh

# Test manual backup
./backup.sh
```

---

## What's Included

✅ **Database Backup**: Full MySQL dump  
✅ **Uploads Backup**: WordPress media files  
✅ **Configuration Backup**: .env, docker-compose.yml, app config  
✅ **Automated Scheduling**: Daily cron job  
✅ **Retention Policy**: 30-day retention  
✅ **Restore Script**: One-command restore  

---

## Usage

### Manual Backup
```bash
./backup.sh
```

Creates: `backups/veriaguide_backup_YYYYMMDD_HHMMSS.tar.gz`

### Automated Backups
```bash
./setup-backup-cron.sh
```

Runs daily at 2 AM (configurable)

### Restore from Backup
```bash
./restore.sh /path/to/backup.tar.gz
```

Restores:
1. Database
2. Uploads
3. Configuration

### View Backups
```bash
ls -lh backups/
```

### View Cron Logs
```bash
tail -f backups/cron.log
```

---

## Backup Contents

Each backup includes:
- **Database**: Complete MySQL dump
- **Uploads**: All WordPress media (wp-content/uploads/)
- **Configuration**: .env, docker-compose.yml, app config

Size: ~50-200MB depending on media

---

## Retention Policy

- **Default**: 30 days
- **Configurable**: Set `RETENTION_DAYS` environment variable
- **Automatic cleanup**: Old backups deleted automatically

---

## Environment Variables

```bash
# In .env or before running scripts
BACKUP_DIR=./backups              # Backup directory
RETENTION_DAYS=30                 # Days to keep backups
DB_CONTAINER=veriaguide_wp_db     # Database container name
DB_NAME=veriaguide_db             # Database name
DB_USER=wp_user                # Database user
DB_PASSWORD=your_password         # Database password
```

---

## Disaster Recovery

### Complete System Failure

```bash
# 1. Restore from backup
./restore.sh /path/to/latest/backup.tar.gz

# 2. Restart services
docker-compose restart

# 3. Verify
curl https://veriaguide.gr/health
```

### Database Corruption

```bash
# 1. Restore database only
docker exec -i veriaguide_wp_db mysql \
  -u "$DB_USER" -p < backups/db_backup_*.sql

# 2. Restart
docker-compose restart
```

---

## Best Practices

1. **Test restores regularly** - Verify backups work
2. **Monitor backup logs** - Check `backups/cron.log`
3. **Store offsite** - Copy backups to remote storage
4. **Document recovery** - Keep recovery procedures updated
5. **Alert on failures** - Monitor backup success

---

## Remote Backup Upload

To upload backups to remote storage:

```bash
# Set remote URL
export BACKUP_REMOTE_URL="https://your-storage.com/upload"

# Run backup (will auto-upload)
./backup.sh
```

---

## Troubleshooting

### Backup fails
```bash
# Check logs
tail -f backups/cron.log

# Verify database password
grep DB_PASSWORD .env

# Test manually
./backup.sh
```

### Restore fails
```bash
# Verify backup file
tar -tzf /path/to/backup.tar.gz

# Check database connection
docker exec veriaguide_wp_db mysql -u "$DB_USER" -p -e "SELECT 1"
```

### Cron not running
```bash
# Check cron jobs
crontab -l

# Check system logs
sudo tail -f /var/log/syslog | grep CRON
```

---

## Zero Downtime

Backups run in background - no downtime!
