#!/bin/bash
# ===========================================================
# 💾 Sauvegarde PostgreSQL — RAP_APP
# ===========================================================

set -e
DATE=$(date +%Y%m%d_%H%M)
BACKUP_DIR="/srv/rap_app/backend/backups"
DB_NAME="rap_app_db"
DB_USER="abd"

mkdir -p $BACKUP_DIR

echo "💾 Sauvegarde de la base $DB_NAME en cours..."
pg_dump -U $DB_USER -d $DB_NAME > "$BACKUP_DIR/backup_$DATE.sql"

if [ $? -eq 0 ]; then
    echo "✅ Sauvegarde réussie à $(date)" | tee -a $BACKUP_DIR/backup.log
    echo "✅ Sauvegarde PostgreSQL réussie sur RAP_APP ($DATE)" | msmtp adserv.fr@gmail.com
else
    echo "⚠️ Échec de la sauvegarde à $(date)" | tee -a $BACKUP_DIR/backup.log
    echo "⚠️ Échec de la sauvegarde PostgreSQL sur RAP_APP ($DATE)" | msmtp adserv.fr@gmail.com
fi

# Nettoyage des sauvegardes de plus de 7 jours
find $BACKUP_DIR -type f -name "*.sql" -mtime +7 -delete
