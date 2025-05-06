# ========================================================
# GESTION DE PROJET DJANGO - CHEAT SHEET (Python3/Pip3)
# ========================================================

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
git commit -m "Ajout des permissions aux viewsets/ajout user à partenaires, et evenements"   
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

- ajouter shéma sawgger

- dosctrings complets, verbose name, help text

- Déplacer les signaux dans signals et services dans services

 - verifier si c'est fait, ou intégrer la journalisation dans un modèle de logs générique en créant un log LogUtilisateur à chaque save() ou suppression via les signaux). 

 - Intégrer des messages d'erreur eplicites dans les models

 - Je souhaite que quand le user chois "autre" qu'il remplisse un champ pour définir "autre"

 - Retirer created_by des models, et les autes champs; puisque dans base model : 
Timestamps :
created_at (DateTime)
updated_at (DateTime)
Tracking utilisateur :
created_by (ForeignKey → User)
updated_by (ForeignKey → User)

Méthodes génériques :
save() (sauf besoin spécifique)
__str__() (sauf personnalisation)

Configuration Meta :
abstract = True
ordering = ['-created_at']
get_latest_by = 'created_at'

 - 