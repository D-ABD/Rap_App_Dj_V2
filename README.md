# 🧾 GUIDE DE DÉPLOIEMENT — Backend Django **RAP_APP**
**VPS Hostinger (Ubuntu 24.04 LTS)** — *Version complète & reproductible*

> **⚠️ Sécurité :** Les secrets (mots de passe DB/SMTP, `SECRET_KEY`, etc.) ont été **remplacés par des placeholders** dans ce guide (`<...>`). Remplis-les avec tes valeurs réelles et garde le fichier `.md` **hors de tout dépôt public**.

---

## 🧠 Informations générales

- **Application** : RAP_APP — Backend Django REST (DRF + PostgreSQL)  
- **Frontend** : séparé (non inclus dans ce déploiement)  
- **Système** : Ubuntu 24.04 LTS  
- **Objectif** : déploiement production sécurisé **HTTPS**, **sauvegarde automatique quotidienne**, **rapports e-mail**

### 📦 Versions recommandées

| Outil     | Version |
|-----------|---------|
| Python    | 3.12    |
| Django    | 5.x     |
| PostgreSQL| 16.x    |
| Gunicorn  | 22.x    |
| Nginx     | 1.24.x  |

---

## ⚙️ 1️⃣ Préparation du serveur

```bash
adduser abd
usermod -aG sudo abd
su - abd
whoami  # → abd
```

---

## 🧩 2️⃣ Installation des dépendances

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git libpq-dev postgresql postgresql-contrib
```

---

## 📁 3️⃣ Installation du projet Django

```bash
mkdir -p ~/rap_app_backend
cd ~/rap_app_backend
python3 -m venv venv
source venv/bin/activate

git clone https://github.com/D-ABD/Rap_App_Dj_V2.git
cd Rap_App_Dj_V2

pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔐 4️⃣ Configuration environnement `.env`

**Chemin** : `/home/abd/rap_app_backend/Rap_App_Dj_V2/.env`

```ini
# --- Django ---
SECRET_KEY=<DJANGO_SECRET_KEY>
DEBUG=False
ALLOWED_HOSTS=rap.adserv.fr,127.0.0.1,localhost

# --- Base de données ---
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rap_app_backend
DB_USER=abd
DB_PASSWORD=<DB_PASSWORD>
DB_HOST=localhost
DB_PORT=5432

# --- CORS/CSRF ---
CORS_ALLOWED_ORIGINS=https://rap.adserv.fr
CSRF_TRUSTED_ORIGINS=https://rap.adserv.fr

# --- Sécurité ---
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# --- Email (Gmail App Password) ---
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=adserv.fr@gmail.com
EMAIL_HOST_PASSWORD=<GMAIL_APP_PASSWORD>
DEFAULT_FROM_EMAIL="RAP_APP <adserv.fr@gmail.com>"
```

Protection :
```bash
chmod 600 /home/abd/rap_app_backend/Rap_App_Dj_V2/.env
```

> 💡 **Conseil** : utilise un **App Password Gmail** (2FA nécessaire), jamais le mot de passe du compte.

---

## 🐘 5️⃣ Base de données PostgreSQL

```sql
-- Connexion
-- (shell) sudo -u postgres psql

CREATE DATABASE rap_app_backend;
CREATE USER abd WITH PASSWORD '<DB_PASSWORD>';
ALTER ROLE abd SET client_encoding TO 'utf8';
ALTER ROLE abd SET default_transaction_isolation TO 'read committed';
ALTER ROLE abd SET timezone TO 'Europe/Paris';
GRANT ALL PRIVILEGES ON DATABASE rap_app_backend TO abd;

-- Quitter psql : \q
```

---

## ⚙️ 6️⃣ Préparation Django

```bash
cd ~/rap_app_backend/Rap_App_Dj_V2
source ../venv/bin/activate

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

---

## 🔥 7️⃣ Service **Gunicorn** (systemd)

**Fichier** : `/etc/systemd/system/gunicorn.service`

```ini
[Unit]
Description=Gunicorn service for RAP_APP
After=network.target

[Service]
User=abd
WorkingDirectory=/home/abd/rap_app_backend/Rap_App_Dj_V2
EnvironmentFile=/home/abd/rap_app_backend/Rap_App_Dj_V2/.env
ExecStart=/home/abd/rap_app_backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 rap_app_project.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Activation :
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
```

---

## 🌐 8️⃣ **Nginx** (reverse proxy)

**Fichier** : `/etc/nginx/sites-available/rap_app`

```nginx
server {
    listen 80;
    server_name rap.adserv.fr;

    location /static/ {
        alias /home/abd/rap_app_backend/Rap_App_Dj_V2/staticfiles/;
    }

    location / {
        include /etc/nginx/proxy_params;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    error_log /var/log/nginx/rap_app_error.log;
    access_log /var/log/nginx/rap_app_access.log;
}
```

Activation :
```bash
sudo ln -s /etc/nginx/sites-available/rap_app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 9️⃣ HTTPS avec **Certbot**

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d rap.adserv.fr
```

> ✅ Le certificat Let’s Encrypt sera auto-renouvelé (via timer systemd).  
> Test : `sudo certbot renew --dry-run`

---

## 🧱 1️⃣0️⃣ Pare-feu (**UFW**)

```bash
sudo apt install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

---

## 💾 1️⃣1️⃣ Scripts utilitaires

### `deploy.sh` (déploiement applicatif)

Fonctions : `git pull` → `pip install` → `migrate` → `collectstatic` → restart services → mail rapport.

> Voir **section 17** pour la version complète (avec logs + mail).

Alias :
```bash
echo "alias deploy='~/deploy.sh'" >> ~/.bashrc
source ~/.bashrc
```

---

### `backup_db.sh` (sauvegarde PostgreSQL + rotation)

- Sauvegarde **compressée** `.sql.gz`  
- **Rotation** : 7 jours  
- Envoi **rapport e-mail**  
- Alias utile : `alias backup='~/backup_db.sh'`

> Implémente `pg_dump` → compression → suppression des sauvegardes > 7j → envoi de mail via `msmtp`.

---

### `restore_db.sh` (restauration)

- Restaure depuis un `.sql.gz`  
- Recréation base + import

> Exemple d’usage :
```bash
./restore_db.sh /home/abd/backups/rap_app_backend_YYYY-MM-DD_HH-MM-SS.sql.gz
```

---

## 🧠 1️⃣2️⃣ Sauvegarde **automatique** via CRON

```bash
crontab -e
# Ajouter la ligne :
0 3 * * * /home/abd/backup_db.sh >> /home/abd/backup_cron.log 2>&1
```

---

## ✉️ 1️⃣3️⃣ Envoi e-mail (**msmtp**)

Installation :
```bash
sudo apt install -y msmtp msmtp-mta mailutils
```

**Fichier** : `~/.msmtprc`
```ini
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        /home/abd/.msmtp.log

account gmail
host smtp.gmail.com
port 587
from adserv.fr@gmail.com
user adserv.fr@gmail.com
password <GMAIL_APP_PASSWORD>

account default : gmail
```

Protection :
```bash
chmod 600 ~/.msmtprc
```

Test :
```bash
echo "Test mail depuis le VPS RAP_APP" | mail -s "Test SMTP VPS" adserv.fr@gmail.com
```

---

## 📊 1️⃣4️⃣ Vérifications & maintenance

**Logs** :
```bash
journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

**Redémarrages** :
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

**Mises à jour** :
```bash
cd /home/abd/rap_app_backend/Rap_App_Dj_V2
git pull
source /home/abd/rap_app_backend/venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
sudo systemctl restart gunicorn
```

---

## 🧩 Variables à **personnaliser** avant tout nouveau déploiement

- `DB_USER`, `DB_PASSWORD`  
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (**App Password**)  
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`  
- Chemins `/home/<user>/rap_app_backend/...`  
- Domaine : `rap.adserv.fr`

---

## 📎 Fichiers de référence à conserver

| Fichier                              | Emplacement                                      |
|--------------------------------------|--------------------------------------------------|
| `.env` (modèle)                      | `/home/abd/rap_app_backend/Rap_App_Dj_V2/`      |
| `.msmtprc`                           | `/home/abd/`                                     |
| `gunicorn.service`                   | `/etc/systemd/system/`                           |
| Nginx site `rap_app`                 | `/etc/nginx/sites-available/rap_app`            |
| `deploy.sh` / `backup_db.sh` / `restore_db.sh` | `/home/abd/`                            |

---

## ✅ État final attendu

| Élément              | Statut | Détails                               |
|---------------------|:-----:|----------------------------------------|
| Django + PostgreSQL | ✅     | Application fonctionnelle              |
| Gunicorn            | ✅     | Service systemd                        |
| Nginx               | ✅     | Reverse proxy                          |
| HTTPS / SSL         | ✅     | Certificat Let’s Encrypt valide        |
| Pare-feu            | ✅     | UFW actif (22/80/443)                  |
| Backups             | ✅     | Automatiques à 03 h, rotation 7 jours  |
| Mail rapports       | ✅     | msmtp + Gmail App Password             |
| Sécurité            | ✅     | Fichiers protégés (.env, .msmtprc)     |

---

## 📈 1️⃣5️⃣ Rapport hebdomadaire de santé du serveur (CPU / RAM / Disque / Backups)

### 🎯 Objectif
Recevoir chaque **lundi 08:00** un e-mail contenant :
- État CPU, mémoire, disque
- Taille de la base PostgreSQL & du dossier backups
- Statut de Gunicorn, Nginx, UFW
- Date & taille de la **dernière sauvegarde**

### ⚙️ 1️⃣ Script `server_report.sh`
```bash
nano ~/server_report.sh
```

**Contenu :**
```bash
#!/bin/bash
# =====================================================
# 📊 Rapport hebdomadaire de santé du serveur RAP_APP
# Auteur : abd
# Envoi automatique chaque lundi 08:00
# =====================================================

# Variables
EMAIL="adserv.fr@gmail.com"
BACKUP_DIR="/home/abd/backups"
DB_NAME="rap_app_backend"

# Fichier temporaire du rapport
REPORT="/tmp/server_report.txt"

echo "===== RAPPORT SERVEUR RAP_APP =====" > $REPORT
echo "Date : $(date)" >> $REPORT
echo "" >> $REPORT

echo "=== 🧠 UTILISATION DU SYSTÈME ===" >> $REPORT
echo "Uptime :" >> $REPORT
uptime >> $REPORT
echo "" >> $REPORT

echo "=== ⚙️ CHARGE CPU ===" >> $REPORT
top -bn1 | grep "Cpu(s)" >> $REPORT
echo "" >> $REPORT

echo "=== 💾 MÉMOIRE ===" >> $REPORT
free -h >> $REPORT
echo "" >> $REPORT

echo "=== 🧱 DISQUE ===" >> $REPORT
df -h / >> $REPORT
echo "" >> $REPORT

echo "=== 🗄️ BASE DE DONNÉES PostgreSQL ===" >> $REPORT
sudo -u postgres psql -d $DB_NAME -c "\l+" | grep $DB_NAME >> $REPORT 2>/dev/null
echo "" >> $REPORT

echo "=== 💽 SAUVEGARDES ===" >> $REPORT
ls -lh $BACKUP_DIR | tail -n 10 >> $REPORT
echo "" >> $REPORT

echo "=== 🚦 SERVICES ===" >> $REPORT
systemctl is-active gunicorn >> $REPORT
systemctl is-active nginx >> $REPORT
sudo ufw status | head -n 10 >> $REPORT
echo "" >> $REPORT

echo "=== 📦 ESPACE UTILISATEUR ===" >> $REPORT
du -sh /home/abd/* 2>/dev/null >> $REPORT
echo "" >> $REPORT

echo "=== ✅ RAPPORT TERMINE ===" >> $REPORT

# Envoi par e-mail
cat $REPORT | mail -s "🧾 Rapport serveur RAP_APP — $(date '+%Y-%m-%d')" $EMAIL
```

**Rendre exécutable :**
```bash
chmod +x ~/server_report.sh
```

**CRON :**
```bash
crontab -e
# Ajouter :
0 8 * * 1 /home/abd/server_report.sh >> /home/abd/server_report.log 2>&1
```

**Test manuel :**
```bash
./server_report.sh
```

---

## 🔒 1️⃣6️⃣ Sécurisation post-déploiement du VPS (`secure_server.sh`)

### 🎯 Objectif
Durcir le serveur Ubuntu **sans interrompre** Django / Gunicorn / Nginx.

**Script :**
```bash
nano ~/secure_server.sh
```
**Contenu :**
```bash
#!/bin/bash
# =====================================================
# 🔒 Sécurisation post-déploiement VPS RAP_APP (Ubuntu 24.04)
# Auteur : abd
# Objectif : durcir le serveur sans interrompre Django/Nginx
# =====================================================
set -euo pipefail

LOG="/home/abd/secure_server_$(date +'%Y-%m-%d_%H-%M-%S').log"
exec > >(tee -a "$LOG") 2>&1

echo "🔹 Sécurisation du serveur — début : $(date '+%F %T')"

# --- 1️⃣ Mise à jour système ---
echo "➡️  Mise à jour complète des paquets..."
sudo apt update && sudo apt upgrade -y && sudo apt autoremove -y

# --- 2️⃣ Sécurisation SSH ---
echo "➡️  Sécurisation SSH..."
SSH_CFG="/etc/ssh/sshd_config"
sudo cp "$SSH_CFG" "${SSH_CFG}.bak_$(date +%s)"

sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' "$SSH_CFG"
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' "$SSH_CFG"
sudo sed -i 's/^#\?PermitEmptyPasswords.*/PermitEmptyPasswords no/' "$SSH_CFG"
sudo systemctl restart ssh

# --- 3️⃣ Pare-feu UFW ---
echo "➡️  Vérification UFW..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status verbose

# --- 4️⃣ Droits & permissions sensibles ---
echo "➡️  Vérification des droits des fichiers sensibles..."
sudo chmod 600 /home/abd/rap_app_backend/Rap_App_Dj_V2/.env
sudo chmod 600 /home/abd/.msmtprc
sudo chown -R abd:www-data /home/abd/rap_app_backend/Rap_App_Dj_V2
sudo find /home/abd/rap_app_backend -type d -exec chmod 755 {} \;
sudo find /home/abd/rap_app_backend -type f -exec chmod 644 {} \;

# --- 5️⃣ Journalisation & rotation des logs ---
echo "➡️  Configuration rotation des logs..."
sudo bash -c 'cat >/etc/logrotate.d/rap_app <<EOF
/var/log/nginx/*.log /home/abd/deploy_logs/*.log /home/abd/backup_cron.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    create 640 root adm
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>/dev/null || true
    endscript
}
EOF'

# --- 6️⃣ Mises à jour automatiques ---
echo "➡️  Activation des mises à jour automatiques..."
sudo apt install -y unattended-upgrades apt-listchanges
sudo dpkg-reconfigure -f noninteractive unattended-upgrades

# --- 7️⃣ Vérification des services critiques ---
echo "➡️  Vérification services..."
for svc in gunicorn nginx postgresql ufw ssh; do
  echo -n "   • $svc : "
  systemctl is-active "$svc" || echo "(⚠️ inactif)"
done

# --- 8️⃣ Nettoyage final ---
echo "➡️  Nettoyage des caches et paquets inutiles..."
sudo apt autoremove -y && sudo apt autoclean -y

echo "✅ Sécurisation terminée avec succès : $(date '+%F %T')"
echo "📄 Rapport complet : $LOG"

# --- (Optionnel) Envoi du rapport par e-mail ---
SUBJECT="RAP_APP — Rapport SECURISATION ($(hostname))"
mail -a "Content-Type: text/plain; charset=UTF-8" -s "$SUBJECT" adserv.fr@gmail.com < "$LOG"
```

**Exécution :**
```bash
chmod +x ~/secure_server.sh
sudo ~/secure_server.sh
```

---

## 🚀 1️⃣7️⃣ Script de déploiement automatisé (`deploy.sh`)

**Objectif :** déploiement fiable avec logs complets + envoi mail succès/échec.

```bash
nano ~/deploy.sh
```
**Contenu :**
```bash
#!/bin/bash
# =====================================================
# 🚀 Déploiement RAP_APP — avec logs + mail (succès/échec)
# =====================================================
set -euo pipefail

# --- Variables ---
PROJECT_DIR="/home/abd/rap_app_backend/Rap_App_Dj_V2"
VENV_DIR="/home/abd/rap_app_backend/venv"
LOG_DIR="/home/abd/deploy_logs"
EMAIL="adserv.fr@gmail.com"
HEALTH_URL=""   # ex: "https://rap.adserv.fr/health/" si un endpoint existe

STAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG="${LOG_DIR}/deploy_${STAMP}.log"

mkdir -p "$LOG_DIR"

# --- Fonction d’envoi d’email ---
notify() {
  local status="$1"
  local subject_prefix="RAP_APP — Rapport DEPLOY (${STAMP}) : $(hostname)"
  if [ "$status" = "OK" ]; then
    SUBJECT="✅ ${subject_prefix}"
  else
    SUBJECT="❌ ${subject_prefix}"
  fi
  mail -a "Content-Type: text/plain; charset=UTF-8" -s "$SUBJECT" "$EMAIL" < "$LOG"
}

# --- Capture stdout/stderr vers le log + console ---
exec > >(tee -a "$LOG") 2>&1

echo "🔹 Début déploiement : $(date '+%F %T')"
echo "📁 Projet : $PROJECT_DIR"
echo "🐍 Venv   : $VENV_DIR"
echo "-----------------------------------"

# Si une étape échoue → envoi mail KO
trap 'echo "❌ Déploiement échoué à $(date)"; notify "KO"' ERR

cd "$PROJECT_DIR"

echo "➡️  Activation venv…"
source "$VENV_DIR/bin/activate"

echo "➡️  Git pull…"
git pull

echo "➡️  pip install…"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "➡️  Migrations…"
python manage.py migrate --noinput

echo "➡️  Collectstatic…"
python manage.py collectstatic --noinput

echo "➡️  Sécurisation .env…"
chmod 600 "$PROJECT_DIR/.env"
sudo chown -R abd:www-data "$PROJECT_DIR"

# --- Vérifie que Gunicorn est exécutable (correctif automatique) ---
if [ ! -x "/home/abd/rap_app_backend/venv/bin/gunicorn" ]; then
    echo "⚠️ Gunicorn n'était pas exécutable — correction..."
    chmod +x /home/abd/rap_app_backend/venv/bin/gunicorn
fi

echo "➡️  Restart Gunicorn & Nginx…"
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "➡️  Statuts services :"
echo -n "   • gunicorn : "; systemctl is-active gunicorn || true
echo -n "   • nginx    : "; systemctl is-active nginx || true

if [ -n "$HEALTH_URL" ]; then
  echo "➡️  Healthcheck : $HEALTH_URL"
  curl -fsS "$HEALTH_URL" && echo "   • OK" || echo "   • (optionnel) endpoint indisponible"
fi

deactivate || true

echo "💾 Espace disque :"
df -h / | tail -n 1

echo "✅ Déploiement terminé : $(date '+%F %T')"
echo "-----------------------------------"

# Mail de succès
notify "OK"
```

**Exécution :**
```bash
chmod +x ~/deploy.sh
# (Option) alias :
echo "alias deploy='~/deploy.sh'" >> ~/.bashrc
source ~/.bashrc

# Lancer :
deploy
```

---

## 🧹 1️⃣8️⃣ Maintenance mensuelle (`monthly_maintenance.sh`)

**Objectif :** nettoyage des backups > 30 j, purge caches, vérif services & disque, mise à jour système, rapport e-mail.

```bash
nano ~/monthly_maintenance.sh
```
**Contenu :**
```bash
#!/bin/bash
# =====================================================
# 🧹 Maintenance mensuelle du serveur RAP_APP
# Auteur : abd
# Objectif : nettoyage, vérification et rapport par e-mail
# =====================================================
set -euo pipefail

EMAIL="adserv.fr@gmail.com"
BACKUP_DIR="/home/abd/backups"
LOG_DIR="/home/abd/maintenance_logs"
STAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG="${LOG_DIR}/maintenance_${STAMP}.log"

mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG") 2>&1

echo "===== RAP_APP — MAINTENANCE MENSUELLE ====="
echo "Date : $(date)"
echo "--------------------------------------------"

# --- 1️⃣ Nettoyage des anciens backups (30 jours) ---
echo "🗑️  Suppression des sauvegardes de plus de 30 jours..."
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +30 -exec rm -v {} \; || true

# --- 2️⃣ Nettoyage du cache APT ---
echo "🧩 Nettoyage du cache APT..."
sudo apt autoremove -y && sudo apt autoclean -y

# --- 3️⃣ Vérification des services critiques ---
echo "🧠 Vérification des services :"
for svc in gunicorn nginx postgresql ufw ssh; do
  status=$(systemctl is-active "$svc")
  echo "   • $svc : $status"
done

# --- 4️⃣ Vérification du disque ---
echo ""
echo "💾 Utilisation du disque :"
df -h /

# --- 5️⃣ Taille du dossier de sauvegardes ---
echo ""
echo "📦 Espace occupé par les sauvegardes :"
du -sh "$BACKUP_DIR" || echo "Dossier non trouvé"

# --- 6️⃣ Journaux système et rotation ---
echo ""
echo "🗂️  Journaux récents :"
sudo journalctl --since "30 days ago" -p 3 -n 20 --no-pager || true

# --- 7️⃣ Mise à jour système (optionnel, sécurisée) ---
echo ""
echo "🔄 Mise à jour du système..."
sudo apt update && sudo apt upgrade -y

# --- 8️⃣ Résumé final ---
echo ""
echo "✅ Maintenance terminée avec succès : $(date)"
echo "Rapport : $LOG"

# --- 9️⃣ Envoi du rapport par e-mail ---
SUBJECT="RAP_APP — Rapport MAINTENANCE (${STAMP}) : $(hostname)"
mail -a "Content-Type: text/plain; charset=UTF-8" -s "$SUBJECT" "$EMAIL" < "$LOG"
```

**Planification CRON :**
```bash
chmod +x ~/monthly_maintenance.sh

crontab -e
# Ajouter :
0 4 1 * * /home/abd/monthly_maintenance.sh >> /home/abd/maintenance_cron.log 2>&1
```

---

## 🧠 1️⃣9️⃣ Supervision complète & automatisée

### 📅 Tableau récapitulatif des automatisations

| Script / Fonction        | Fréquence                 | Type d’action                                   | Rapport e-mail | Log local                               | Objectif |
|--------------------------|---------------------------|--------------------------------------------------|----------------|-----------------------------------------|----------|
| `backup_db.sh`           | Tous les jours à 03h00    | Sauvegarde PostgreSQL (.sql.gz) + rotation 7 j  | ✅ Oui         | `/home/abd/backup_cron.log`             | Préserver DB |
| `server_report.sh`       | Tous les lundis 08h00     | Rapport CPU / RAM / disque / services           | ✅ Oui         | `/home/abd/server_report.log`           | Santé système |
| `secure_server.sh`       | Manuel                    | Durcissement serveur, logrotate, maj auto       | ✅ Oui         | `/home/abd/secure_server_*.log`         | Sécuriser |
| `deploy.sh`              | À la demande (`deploy`)   | Déploiement complet Django + restart services   | ✅ Oui         | `/home/abd/deploy_logs/*.log`           | Mettre à jour |
| `monthly_maintenance.sh` | 1er du mois à 04h00       | Nettoyage complet & maj système                 | ✅ Oui         | `/home/abd/maintenance_logs/*.log`      | Entretien |

### 🔐 Composants de sécurité actifs

| Élément            | Statut | Détails                                           |
|-------------------|:-----:|----------------------------------------------------|
| UFW Firewall      | ✅     | Ports 22 / 80 / 443 uniquement                    |
| SSH               | ✅     | Root interdit, mot de passe requis                |
| `.env` & `.msmtprc` | ✅   | `chmod 600`, propriétaire `abd`                   |
| unattended-upgrades | ✅   | Mises à jour automatiques actives                 |
| logrotate         | ✅     | Rotation hebdomadaire des journaux                |
| Certbot           | ✅     | Certificat Let’s Encrypt auto-renouvelé           |
| msmtp             | ✅     | Emails via Gmail App Password                     |

### 🧩 Emplacement des fichiers critiques

| Fichier / Dossier       | Rôle                           | Emplacement                                         |
|-------------------------|--------------------------------|-----------------------------------------------------|
| `.env`                  | Config Django                  | `/home/abd/rap_app_backend/Rap_App_Dj_V2/.env`     |
| `.msmtprc`              | SMTP Gmail (mailutils)         | `/home/abd/.msmtprc`                                |
| `gunicorn.service`      | Service Django                 | `/etc/systemd/system/gunicorn.service`              |
| `rap_app` (Nginx site)  | Reverse proxy                  | `/etc/nginx/sites-available/rap_app`                |
| `deploy.sh`             | Déploiement Django             | `/home/abd/deploy.sh`                               |
| `backup_db.sh`          | Sauvegarde quotidienne         | `/home/abd/backup_db.sh`                            |
| `restore_db.sh`         | Restauration DB                | `/home/abd/restore_db.sh`                           |
| `server_report.sh`      | Rapport hebdomadaire           | `/home/abd/server_report.sh`                        |
| `secure_server.sh`      | Sécurisation VPS               | `/home/abd/secure_server.sh`                        |
| `monthly_maintenance.sh`| Maintenance mensuelle          | `/home/abd/monthly_maintenance.sh`                  |

---

## 📈 Cycle complet de vie du serveur

| Étape                         | Action                                                    | Fréquence            |
|------------------------------|-----------------------------------------------------------|----------------------|
| Déploiement (`deploy.sh`)    | Met à jour l’app, restart services, mail rapport         | À la demande         |
| Sauvegarde (`backup_db.sh`)  | Sauvegarde DB + rotation 7 jours                         | Quotidien 03h        |
| Rapport (`server_report.sh`) | État système + services                                   | Lundi 08h            |
| Maintenance (`monthly_maintenance.sh`) | Nettoyage + maj système                        | 1er du mois 04h      |
| Sécurisation (`secure_server.sh`) | Vérification / durcissement OS                   | Après déploiement/maj |

---

## 💡 Bonnes pratiques d’exploitation

- Lancer `sudo ~/secure_server.sh` **après chaque grosse mise à jour** système  
- Déployer avec **`deploy` (alias)** plutôt que manuellement  
- Vérifier `journalctl -u gunicorn -f` et `sudo tail -f /var/log/nginx/error.log` **après chaque déploiement**  
- Surveiller les **emails** (deploy / backup / maintenance / health) : `adserv.fr@gmail.com`  
- Conserver **3 derniers backups** `.sql.gz` **hors du VPS** (stockage externe)  
- Tester le certificat SSL : `sudo certbot renew --dry-run` (tous les 3 mois)  
- Vérifier l’espace disque régulièrement : `df -h /`  

---

## 🏁 Résumé final

| Domaine              | Statut | Détails                                      |
|---------------------|:-----:|-----------------------------------------------|
| Déploiement continu | ✅     | Automatisé avec logs et mails                 |
| Sauvegarde quotidienne | ✅  | Cron 03h + rotation 7 jours                   |
| Supervision hebdo   | ✅     | Mail chaque lundi 08h                         |
| Maintenance mensuelle | ✅   | Cron 04h le 1er du mois                       |
| Sécurisation serveur| ✅     | SSH, UFW, updates, permissions                |
| Monitoring complet  | ✅     | CPU, mémoire, disque, services                |
| Notifications e-mail| ✅     | msmtp + Gmail App Password                    |

---

**Fin du guide — RAP_APP Backend (Django + DRF + PostgreSQL)**
