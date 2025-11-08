#!/bin/bash
# ===========================================================
# 🚀 DEPLOY.SH — Déploiement automatique du backend RAP_APP
# ===========================================================

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
