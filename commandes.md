# ========================================================
# GESTION DE PROJET DJANGO - CHEAT SHEET (Python3/Pip3)
# ========================================================

# --------------------------
# 1. ENVIRONNEMENT VIRTUEL
# --------------------------

# Créer et activer l'environnement
python3 -m venv env                   # Création
source env/bin/activate               # Activation (Linux/Mac)
# .\env\Scripts\activate              # Activation (Windows)

# Gestion des dépendances
pip3 install --upgrade pip            # Mettre à jour pip
pip3 install django                   # Installer Django
pip3 freeze > requirements.txt        # Exporter les dépendances
pip3 install -r requirements.txt      # Importer les dépendances

deactivate                            # Désactiver l'environnement

# --------------------------
# 2. GESTION DE PROJET
# --------------------------

# Démarrer un nouveau projet
django-admin startproject nom_projet   # Création projet
cd nom_projet                         # Se placer dans le projet

# Lancer le serveur de développement
python3 manage.py runserver           # Port par défaut (8000)
python3 manage.py runserver 8080      # Spécifier un port

# --------------------------
# 3. APPLICATIONS & MODÈLES
# --------------------------

# Créer une nouvelle application
python3 manage.py startapp mon_app

# Gestion des migrations
python3 manage.py makemigrations      # Créer les migrations
python3 manage.py migrate             # Appliquer les migrations
python3 manage.py showmigrations      # Voir les migrations

# Administration
python3 manage.py createsuperuser     # Créer un superuser

# --------------------------
# 4. GESTION GIT
# --------------------------

# Configuration initiale
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin URL_DU_DEPOT.git
git push -u origin main

# Workflow quotidien
git status                           # Vérifier les modifications
git add .                            # Ajouter tous les fichiers
git commit -m "Description claire"   # Créer un commit
git push origin main                 # Pousser les modifications

# --------------------------
# 5. PRODUCTION
# --------------------------

# Fichiers statiques
python3 manage.py collectstatic --noinput  # Collecter les statics
rm -rf staticfiles/                       # Nettoyer (si nécessaire)

# Vérifications
python3 manage.py check --deploy          # Vérifier la configuration prod

# --------------------------
# 6. COMMANDES UTILES
# --------------------------

# Shell Django (avec extensions)
python3 manage.py shell_plus              # Nécessite django-extensions

# Nettoyage
find . -name "*.pyc" -exec rm -f {} \;    # Supprimer les .pyc
find . -type d -name "__pycache__" -exec rm -rf {} \;  # Nettoyer les caches

# Backup base de données
python3 manage.py dumpdata > backup.json  # Exporter
python3 manage.py loaddata backup.json    # Importer

# --------------------------
# 7. DÉMARRAGE RAPIDE
# --------------------------

# Tout en une commande (pour nouveau projet)
git init && python3 -m venv env && source env/bin/activate && \
pip3 install django && django-admin startproject mon_projet && \
cd mon_projet && python3 manage.py runserver