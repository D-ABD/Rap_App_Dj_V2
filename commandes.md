# ========================================================
# GESTION DE PROJET DJANGO - CHEAT SHEET (Python3/Pip3)
# ========================================================

python3 manage.py runserver 0.0.0.0:8000

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
git commit -m "préparation pour front/ mise en place des fichiers admin"   
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



Je souhaite que tu m’aides à écrire des serializers et des viewsets ultra complets pour mon application Django.
⚠️ Les tests des modèles sont déjà faits et validés.

Pour chaque modèle que je vais t’envoyer :

🔹 Serializers :
Expose tous les champs du modèle, y compris :

Les champs standards,

Les méthodes @property utiles au frontend,

Les listes de choix (choices) avec un affichage clair dans Swagger (clé + libellé).

Ajoute des messages d'erreur personnalisés pour chaque champ requis ou mal renseigné.
Exemple : "Création de la formation échouée : vous devez renseigner le statut."

Ajoute des messages de succès exploitables côté frontend.
Exemple : "Formation créée avec succès."

Utilise @extend_schema pour que Swagger/OpenAPI :

Affiche les paramètres attendus,

Montre les formats des requêtes et des réponses,

Propose des exemples concrets testables dans l’interface Swagger.

🔹 ViewSets :
Complet, avec :

Permissions,

Filtres personnalisés (filterset_class),

Recherche (search_fields) et tri (ordering_fields).

🔹 Tests :
Tests unitaires des serializers :

Cas de succès,

Cas d’échec (avec vérification des messages d'erreurs).

Tests unitaires des viewsets :

Lecture,

Création (si autorisée),

Filtres, recherche, tri.

🔐 L’objectif est de protéger le frontend, développé par une personne débutante qui n’aura pas accès aux modèles Django.
Tous les comportements doivent donc être clairs, testables et sans ambiguïté via Swagger.

👉 Je vais t’envoyer les modèles un par un.
Dans un premier temps, contente-toi de les enregistrer en mémoire.
Quand je te dirai "GO", tu pourras commencer à générer le code.





# Liste de contrôle exhaustive pour les modèles Django

## 1. Structure et héritage des modèles

- [ ] **Éviter la duplication des champs hérités**
  - Retirer `created_at`, `updated_at`, `created_by`, `updated_by` des modèles enfants s'ils sont déjà définis dans `BaseModel`
  - Implémenter une méthode dans `BaseModel` pour récupérer l'utilisateur actuel (`get_current_user()`)

- [ ] **Cohérence entre modèles**
  - Les champs communs ont des noms et types cohérents dans tous les modèles
  - Les relations entre modèles sont correctement définies (ForeignKey, ManyToMany, etc.)

## 2. Champs et validations

- [ ] **Tous les champs ont**:
  - `verbose_name` explicite (pour l'interface d'admin)
  - `help_text` pour l'aide contextuelle
  - Valeurs par défaut explicites pour les champs numériques (`default=0` au lieu de `null=True`)

- [ ] **Validations robustes**:
  - Méthode `clean()` implémentée pour valider la cohérence (ex: `start_date` < `end_date`)
  - Gestion des cas limites dans les calculs (division par zéro, etc.)
  - Pour les champs "autre", ajouter un champ texte conditionnel (`autre_precision` activé si choix="autre")

## 3. Performance et indexation

- [ ] **Indexation appropriée**:
  - Indexes sur les champs fréquemment utilisés pour le filtrage et le tri
  - Indexes composites pour les requêtes communes
  ```python
  exemples: class Meta:
      indexes = [
          models.Index(fields=['date_debut', 'date_fin']),
          models.Index(fields=['centre', 'annee']),
      ]
  ```

- [ ] **Optimisation des requêtes**:
  - Utilisation d'`annotate()` et `F()` pour les calculs au niveau SQL
  - Éviter les requêtes N+1 avec `select_related()` et `prefetch_related()`

## 4. Documentation et lisibilité

- [ ] **Documentation complète**:
  - Docstrings de classe expliquant le rôle du modèle et ses cas d'usage
  - Docstrings pour toutes les méthodes (y compris paramètres et valeurs de retour)
  - Commentaires sur la logique métier complexe

- [ ] **Méthodes de représentation**:
  - Méthode `__str__()` claire et informative
  - Implémentation de `__repr__()` pour le débogage si nécessaire

## 5. API et sérialisation

- [ ] **Méthodes de sérialisation**:
  - `to_serializable_dict()` implémentée dans tous les modèles
  - Conversion appropriée des objets complexes (dates, relations, etc.)
  - Gestion des champs sensibles (exclusion des données confidentielles)

- [ ] **Navigation**:
  - Méthode `()` pour les liens dans l'admin et l'API
  - Schéma Swagger généré pour la documentation de l'API

## 6. Journalisation et signaux

- [ ] **Architecture propre pour les signaux**:
  - Signaux déplacés dans un module dédié (`signals.py`)
  - Implémentation de `ready()` dans `apps.py` pour connecter les signaux

- [ ] **Journalisation complète**:
  - Modèle `LogUtilisateur` pour suivre toutes les actions CRUD
  - Signaux pour les opérations `post_save` et `pre_delete`
  - Format standardisé pour les messages de journalisation

```python

## 7. Gestion des erreurs

- [ ] **Messages d'erreur**:
  - Messages d'erreur clairs et exploitables dans tous les modèles
  - Codes d'erreur standardisés pour le frontend
  - Traductions des messages d'erreur (si multilangue)


## 9. Éléments supplémentaires

- [ ] **Caching**:
  - Définir des stratégies de cache pour les données fréquemment accédées
  - Implémenter `@cached_property` pour les calculs coûteux

- [ ] **Gestion des versions**:
  - Système de versionnage pour les modifications importantes des modèles
  - Historique des changements (`django-simple-history`)

- [ ] **Tests unitaires**:
  - Tests de validation pour les méthodes personnalisées
  - Tests de comportement pour les signaux
  - Tests d'intégration pour les interactions entre modèles





🔹 1. Modèles fondamentaux (peu ou pas de dépendances) :
statut.py ✅ (déjà traité)

types_offre.py ✅ (déjà traité)

base.py (abstrait, pas besoin de serializer dédié)

🔹 2. Référentiels et entités simples :
centres.py (nécessaire pour formations)

custom_user.py (utilisé partout comme created_by, updated_by)

logs.py (utile pour audit, mais souvent read-only)

🔹 3. Entités secondaires liées aux formations :
partenaires.py

commentaires.py

documents.py

evenements.py

🔹 4. Entité centrale :
formations.py (le cœur du projet, dépend de statut, type_offre, centre, etc.)

🔹 5. Entités métier complémentaires :
prospection.py + historique_prospection (dépendent de partenaire)

rapports.py (souvent basé sur des exports ou des vues)

prepacomp.py (liée à centre et semaine)

vae_jury.py (liée à user, centre, statut, etc.)

