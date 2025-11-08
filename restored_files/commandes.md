# ========================================================
# GESTION DE PROJET DJANGO - CHEAT SHEET (Python3/Pip3)
# ========================================================
 
python3 manage.py check    
python3 manage.py makemigrations 
python3 manage.py migrate 
En local :
cp .env.local .env
python3 manage.py runserver

python3 manage.py runserver 0.0.0.0:8000
python3 manage.py spectacular --file schema.yaml

-- Étape 1 : Se connecter à la base postgres par défaut
-- Vous devez exécuter ce script en étant connecté à la base "postgres"

-- Déconnexion des utilisateurs connectés à la base (optionnel mais recommandé si la base est utilisée)

REVOKE CONNECT ON DATABASE rap_app_backend FROM public;
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'rap_app_backend'
  AND pid <> pg_backend_pid();

-- Étape 2 : Supprimer la base si elle existe
DROP DATABASE IF EXISTS rap_app_backend;

-- Étape 3 : Créer la base
CREATE DATABASE rap_app_backend
  WITH OWNER = rap_user
       ENCODING = 'UTF8'
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE = 'en_US.UTF-8'
       TEMPLATE = template0;

-- Étape 4 : Accorder les droits
-- Si l’utilisateur rap_user n'existe pas, créez-le (sinon commentez la ligne suivante)
-- CREATE USER rap_user WITH PASSWORD 'your_password';

-- S'assurer que l'utilisateur a tous les droits sur la base
GRANT ALL PRIVILEGES ON DATABASE rap_app_backend TO rap_user;



# --------------------------
# 1. ENVIRONNEMENT VIRTUEL
# --------------------------

# Créer et activer l'environnement
# Création
# Activation (Linux/Mac)
# Activation (Windows)
python3 -m venv env                   
source env/bin/activate               
.\env\Scripts\activate              

# Gestion des dépendances
# Mettre à jour pip
# Installer Django
# Exporter les dépendances
# Importer les dépendances
# Désactiver l'environnement
pip3 install --upgrade pip            
pip3 install django                   
pip3 freeze > requirements.txt        
pip3 install -r requirements.txt      
deactivate                           

# --------------------------
# 2. GESTION DE PROJET
# --------------------------

# Démarrer un nouveau projet
# Création projet
# Se placer dans le projet
django-admin startproject nom_projet   
cd nom_projet                         

# Lancer le serveur de développement
# Port par défaut (8000)
# Spécifier un port
python3 manage.py runserver           
python3 manage.py runserver 8080      

# --------------------------
# 3. APPLICATIONS & MODÈLES
# --------------------------

# Créer une nouvelle application
python3 manage.py startapp mon_app

# Gestion des migrations
# Créer les migrations
# Appliquer les migrations
# Voir les migrations
python3 manage.py makemigrations      
python3 manage.py migrate             
python3 manage.py showmigrations      

# Administration
# Créer un superuser
python3 manage.py createsuperuser     

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
# Vérifier les modifications
# Ajouter tous les fichiers
# Créer un commit
# Pousser les modifications
git status                           
git add .                            
git commit -m "Ajout des models, serializers et viewsets, pour atelier_tre; Appairage et candidats. versions à vérifier"   
git push origin main                 







# --------------------------
# 5. PRODUCTION
# --------------------------

# Fichiers statiques
# Collecter les statics
# Nettoyer (si nécessaire)
python3 manage.py collectstatic --noinput  
rm -rf staticfiles/                       

# Vérifier la configuration
python3 manage.py check --deploy           

# --------------------------
# 6. COMMANDES UTILES
# --------------------------

# Shell Django (avec extensions)
python3 manage.py shell_plus              

# Nettoyage
# Nécessite django-extensions
# Supprimer les .pyc
find . -name "*.pyc" -exec rm -f {} \;    
find . -type d -name "__pycache__" -exec rm -rf {} \;  # Nettoyer les caches

# Backup base de données
# Exporter
# Importer
python3 manage.py dumpdata > backup.json  
python3 manage.py loaddata backup.json    

# --------------------------
# 7. DÉMARRAGE RAPIDE
# --------------------------

# Tout en une commande (pour nouveau projet)
git init && python3 -m venv env && source env/bin/activate && \
pip3 install django && django-admin startproject mon_projet && \
cd mon_projet && python3 manage.py runserver

# --------------------------
# 8. TESTS
# --------------------------
Lancer les tests
python3 manage.py test
python3 manage.py test nom_de_lapp
python3 manage.py test nom_de_lapp.tests.NomDeLaClasseDeTest
python3 manage.py test nom_de_lapp.tests.NomDeLaClasseDeTest.nom_methode
exemple : python3 manage.py test accounts.tests.UserSerializerTest 

python3 manage.py test rap_app.tests.test_model


# --------------------------
#Models
# --------------------------
Commande: python3 manage.py verifie_modeles

 Hook Git automatique

Créer le hook :

echo -e '#!/bin/bash\nnpm run precommit' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit


➡️ Chaque git commit exécutera automatiquement les vérifications avant validation.

🚀 1️⃣3️⃣ AUTOMATISATION DU DÉPLOIEMENT
🔹 Fichier scripts/deploy_front.sh
#!/bin/bash
set -e
echo "🚀 Build & déploiement du frontend vers production..."

npm run lint && npm run type-check
npm run build

ssh root@147.93.126.119 "rm -rf /srv/rap_app_front/*"
scp -r dist/* root@147.93.126.119:/srv/rap_app_front/
ssh root@147.93.126.119 "sudo systemctl reload nginx"

echo "✅ Déploiement terminé avec succès !"

🔹 Rendre exécutable
chmod +x scripts/deploy_front.sh

🧠 1️⃣4️⃣ BONNES PRATIQUES DE MAINTENANCE

Toujours lancer npm run precommit avant tout commit important.

Toujours exécuter npm run build && npm run deploy pour publier en prod.

Ne jamais modifier manuellement le dossier /srv/rap_app_front côté serveur.

Si un build échoue : vérifier le log de build local (vite build) avant de retenter le déploiement.

En cas de doute, tester localement le build avec :

npm run preview


→ Cela simule exactement ce que Nginx servira en production.


