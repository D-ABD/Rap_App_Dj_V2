# 🧾 GUIDE DE DÉPLOIEMENT — Backend Django RAP_APP

**Serveur :** VPS Hostinger (Ubuntu 24.04 LTS)  
**Chemin racine :** `/srv/rap_app/backend/`  
**Nom d’utilisateur :** `abd`  
**Dernière mise à jour :** 08/11/2025  

⚠️ **Tous les secrets (mot de passe DB, Gmail App Password, SECRET_KEY, etc.) sont remplacés par des placeholders `<...>`.**  
**Ne publie jamais ce fichier dans un dépôt public.**

---

## 🧠 Informations générales

- **Application :** RAP_APP (Django REST + PostgreSQL)  
- **Frontend :** hébergé séparément (React)  
- **Serveur :** Ubuntu 24.04 LTS sur Hostinger VPS  
- **Nom de domaine :** [https://rap.adserv.fr](https://rap.adserv.fr)

**Objectifs :**
- Déploiement automatique sécurisé (`deploy.sh`)
- Supervision API/DB (`check_alert.sh`)
- Sauvegardes quotidiennes PostgreSQL (`backup_db.sh`)
- Alertes & rapports e-mail (`msmtp`)

---

## ⚙️ 1️⃣ Arborescence principale

/srv/rap_app/backend/
│
├── backups/ → Sauvegardes automatiques PostgreSQL (.sql)
├── logs/ → Logs d’audit / alertes / erreurs
├── utils/
│ ├── backup_db.sh → Script de backup DB
│ ├── check_alert.sh → Vérifie API & DB, envoie alertes e-mail
│ └── (futurs scripts)
│
├── rap_app/ → Code Django principal
├── rap_app_project/ → Projet Django (settings, wsgi)
├── venv/ → Environnement virtuel Python 3.12
├── manage.py
├── deploy.sh → Déploiement automatique complet
└── requirements.txt

makefile
Copier le code

---

## 🔐 2️⃣ Fichier d’environnement `.env`

**Chemin :** `/srv/rap_app/backend/.env`

```bash
# === DJANGO CONFIGURATION ===
SECRET_KEY=<SECRET_KEY>
DEBUG=False
ALLOWED_HOSTS=rap.adserv.fr,127.0.0.1,localhost,147.93.126.119

# === BASE DE DONNÉES ===
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rap_app_backend
DB_USER=abd
DB_PASSWORD=<DB_PASSWORD>
DB_HOST=localhost
DB_PORT=5432

# === CORS / CSRF ===
CSRF_TRUSTED_ORIGINS=https://rap.adserv.fr,https://app.adserv.fr
CORS_ALLOWED_ORIGINS=https://rap.adserv.fr,https://app.adserv.fr
CORS_ALLOW_CREDENTIALS=True

# === SÉCURITÉ ===
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# === EMAIL (Gmail App Password) ===
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=adserv.fr@gmail.com
EMAIL_HOST_PASSWORD=<GMAIL_APP_PASSWORD>
DEFAULT_FROM_EMAIL="RAP_APP Notifications <adserv.fr@gmail.com>"
Protection :

bash
Copier le code
chmod 600 /srv/rap_app/backend/.env
🐘 3️⃣ Base de données PostgreSQL
Instance locale (port 5432)

sql
Copier le code
CREATE DATABASE rap_app_backend;
CREATE USER abd WITH PASSWORD '<DB_PASSWORD>';
GRANT ALL PRIVILEGES ON DATABASE rap_app_backend TO abd;
ALTER ROLE abd SET timezone TO 'Europe/Paris';
Vérification :

bash
Copier le code
sudo -u postgres psql -l | grep rap
🧱 4️⃣ Migration et collecte statiques
bash
Copier le code
cd /srv/rap_app/backend
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
🔥 5️⃣ Services systèmes
🧩 Gunicorn
Service : /etc/systemd/system/gunicorn_rapapp.service

ini
Copier le code
[Unit]
Description=gunicorn daemon for rap_app
After=network.target

[Service]
User=abd
Group=www-data
WorkingDirectory=/srv/rap_app/backend
EnvironmentFile=/srv/rap_app/backend/.env
ExecStart=/srv/rap_app/backend/venv/bin/gunicorn \
  --access-logfile - \
  --workers 3 \
  --bind unix:/srv/rap_app/backend/gunicorn_rapapp.sock \
  rap_app_project.wsgi:application

[Install]
WantedBy=multi-user.target
Activation :

bash
Copier le code
sudo systemctl daemon-reload
sudo systemctl enable gunicorn_rapapp
sudo systemctl restart gunicorn_rapapp
🌐 Nginx
Configuration : /etc/nginx/conf.d/rap_app.conf

nginx
Copier le code
server {
    listen 80;
    server_name rap.adserv.fr 147.93.126.119;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /srv/rap_app/backend/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/srv/rap_app/backend/gunicorn_rapapp.sock;
    }

    client_max_body_size 50M;
}
Vérification :

bash
Copier le code
sudo nginx -t && sudo systemctl reload nginx
✉️ 6️⃣ Envoi e-mail — msmtp
Fichier : /home/abd/.msmtprc

bash
Copier le code
defaults
auth on
tls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile /home/abd/.msmtp.log

account gmail
host smtp.gmail.com
port 587
from adserv.fr@gmail.com
user adserv.fr@gmail.com
password <GMAIL_APP_PASSWORD>

account default : gmail
Protection :

bash
Copier le code
chmod 600 ~/.msmtprc
Test :

bash
Copier le code
echo "Hello depuis msmtp." | mail -s "Test SMTP VPS" adserv.fr@gmail.com
💾 7️⃣ Sauvegarde automatique — backup_db.sh
Chemin : /srv/rap_app/backend/utils/backup_db.sh

bash
Copier le code
#!/bin/bash
BACKUP_DIR="/srv/rap_app/backend/backups"
DB_NAME="rap_app_backend"
USER="abd"
EMAIL="adserv.fr@gmail.com"
DATE=$(date +"%Y%m%d_%H%M")

mkdir -p "$BACKUP_DIR"
FILE="$BACKUP_DIR/backup_${DATE}.sql"

PGPASSWORD='<DB_PASSWORD>' pg_dump -U $USER -h localhost $DB_NAME > "$FILE"
echo "Sauvegarde PostgreSQL terminée : $FILE" | mail -s "Backup RAP_APP OK" $EMAIL

find "$BACKUP_DIR" -type f -mtime +7 -delete
Cron :

bash
Copier le code
# 0 3 * * * /srv/rap_app/backend/utils/backup_db.sh >> /srv/rap_app/backend/logs/backup.log 2>&1
🩺 8️⃣ Supervision — check_alert.sh
Chemin : /srv/rap_app/backend/utils/check_alert.sh

Fonctions :

Vérifie disponibilité PostgreSQL & API

Envoie mail “DOWN” / “RESTORED”

Écrit dans /srv/rap_app/backend/logs/check_alert.log

Logs :

bash
Copier le code
tail -n 20 /srv/rap_app/backend/logs/check_alert.log
🚀 9️⃣ Déploiement automatique — deploy.sh
Chemin : /srv/rap_app/backend/deploy.sh

bash
Copier le code
#!/bin/bash
set -e
cd /srv/rap_app/backend

echo "--------------------------------------------"
echo "🔄 Déploiement RAP_APP — $(date)"
echo "--------------------------------------------"

echo "📦 Mise à jour du code..."
git pull origin main

echo "🐍 Activation de l'environnement..."
source venv/bin/activate

echo "📚 Installation des dépendances..."
pip install -r requirements.txt --no-cache-dir

echo "🗄️ Migrations..."
python manage.py migrate --noinput

echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "♻️ Redémarrage de Gunicorn & Nginx..."
sudo systemctl restart gunicorn_rapapp.service
sudo systemctl reload nginx

echo "✅ Déploiement terminé avec succès."
echo "--------------------------------------------"
sudo systemctl status gunicorn_rapapp.service --no-pager | head -n 10
⏰ 1️⃣0️⃣ Automatisations Cron
Fréquence	Script	Fonction
*/10 * * * *	/srv/rap_app/backend/utils/check_alert.sh	Vérification API/DB + alertes mail
0 3 * * *	/srv/rap_app/backend/utils/backup_db.sh	Sauvegarde PostgreSQL quotidienne
(optionnel)	/srv/rap_app/backend/deploy.sh	Déploiement manuel

📊 1️⃣1️⃣ Vérification & maintenance
bash
Copier le code
sudo systemctl status gunicorn_rapapp
sudo systemctl status nginx
sudo journalctl -u gunicorn_rapapp -f
sudo tail -f /var/log/nginx/error.log
🧩 1️⃣2️⃣ Points à retenir
Élément	Statut	Détails
Django Backend	✅	Fonctionnel
PostgreSQL	✅	En local, base rap_app_backend
Gunicorn	✅	Service actif via systemd
Nginx	✅	Reverse proxy configuré
HTTPS	🔜	Prévu (Certbot optionnel)
msmtp (mail)	✅	Opérationnel
Sauvegardes	✅	Cron quotidien, rotation 7 jours
Monitoring	✅	Alertes “DB/API down” + auto mail
Deploy	✅	Script stable & testé

🧱 1️⃣3️⃣ Prochaines améliorations (à planifier)
Tâche	Description
/api/health/	Créer endpoint de santé Django (status + DB)
Certbot HTTPS	Activer SSL Let’s Encrypt
server_report.sh	Rapport hebdo CPU / RAM / backup
monthly_maintenance.sh	Nettoyage + maj système + rapport
restore_db.sh	Automatisation restauration base

🏁 Résumé final
Composant	État	Emplacement
.env	✅	/srv/rap_app/backend/.env
deploy.sh	✅	/srv/rap_app/backend/deploy.sh
check_alert.sh	✅	/srv/rap_app/backend/utils/
backup_db.sh	✅	/srv/rap_app/backend/utils/
gunicorn_rapapp.service	✅	/etc/systemd/system/
nginx.conf	✅	/etc/nginx/conf.d/rap_app.conf
.msmtprc	✅	/home/abd/.msmtprc
crontab	✅	backup + check_alert

✅ Environnement stable au 08/11/2025
Tous les services critiques sont actifs, supervisés et automatisés.
Tu disposes d’un backend résilient, sauvegardé et redéployable en un seul script.