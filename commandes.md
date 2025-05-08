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
git commit -m "Amélioration gestion des user(base-model)/ integration du user save das les models enfants/ Correction des models"   
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

Voir si j'ai besoin de plus de signaux (formation modif en teps reel / logger crud )
Message d'erreur dans tous les models(pour frontend)
Verifier dynamiquement la présence de certains attributs ou méthodes dans tous tes modèles Django: 
Fichier:  rap_app_project/rap_app/management/commands/verifie_modeles.py

Commande: python3 manage.py verifie_modeles

- ajouter shéma sawgger
-  Ajouter to_serializable_dict() dans tous les models

- dosctrings complets, verbose name, help text

- Déplacer les signaux dans signals et services dans services

 - verifier si c'est fait, ou intégrer la journalisation dans un modèle de logs générique en créant un log LogUtilisateur à chaque save() ou suppression via les signaux). 

 - Intégrer des messages d'erreur eplicites dans les models

 - Je souhaite que quand le user chois "autre" qu'il remplisse un champ pour définir "autre"

 - Retirer created_by, updated_by, created_at, created_by  des models enfnts, puisque déjà dans base model : Methode dans base model pour appeler le user dans les models enfants


Méthodes génériques :
save() (sauf besoin spécifique)
__str__() (sauf personnalisation)

Configuration Meta :
abstract = True
ordering = ['-created_at']
get_latest_by = 'created_at'

 - 
 # --------------------------------------------------------
# Corrections et verifications importantes pour formations
# --------------------------------------------------------


 - je souhaite que tu verifie formation. à chaque fois je vais te le montrer avec un des models qui a une clé avec lui. je veux que tu verifie les fonctionnalités entre les deux models, la cohérence et identifie les erreurs...

 ✅ 1. Cohérence des champs
 Tous les ForeignKey pointent vers des modèles existants (Centre, Statut, TypeOffre, Partenaire).

 Les champs numériques ont des default explicites (évite les None).

 Les noms de champs sont cohérents et explicites.

 Les verbose_name sont définis pour la lisibilité dans l’admin.

 ✅ 2. Intégrité des données
 La méthode clean() vérifie la cohérence entre start_date et end_date.

 Le save() utilise full_clean() pour valider l’objet.

 Les créations d’HistoriqueFormation sont encapsulées dans une transaction atomique.

 Les calculs de propriétés (taux_saturation, places_disponibles, etc.) gèrent bien les cas de division par zéro.

 ✅ 3. Logique métier et calculs
 total_places, total_inscrits, taux_transformation, etc. sont bien séparés et testables.

 Les méthodes add_commentaire() et add_evenement() gèrent bien les mises à jour liées (dernier_commentaire, nombre_evenements) et la journalisation.

 Les méthodes get_*() (commentaires, documents, événements, partenaires) sont bien définies pour le frontend.

 ✅ 4. Compatibilité DRF / API
 La méthode to_serializable_dict() transforme proprement les champs complexes (Model, date) pour l’API.

 Les objets liés (centre, statut, etc.) sont sérialisés avec id et name → utile pour les dropdowns côté React.

 Le modèle a une get_absolute_url() pour le routing dans l’interface admin ou l’API.

✅ 5. Historisation
 Historisation fine des champs dans le save(), avec HistoriqueFormation.

 L’utilisateur est bien transmis via user=..., et conservé avec created_by.

 La méthode __str__() est explicite et utile pour les logs/admin.

 Les changements détectés sont intelligemment différenciés (if old_val != new_val).

 ✅ 6. Indexation et performances
 Des indexes sont définis sur les champs start_date, end_date, nom.

 Le manager personnalisé FormationManager ajoute des méthodes utiles pour les requêtes (actives, à venir, tri, etc.).

 Les requêtes dans formations_a_recruter() utilisent annotate() + F() pour des calculs SQL efficaces.

 Les propriétés comme taux_transformation, taux_saturation, total_places, etc. :

 Des indexes sont définis sur les champs qui seront filtrer

 to_serializable_dict()

 Vérifier get_default_color() : Implémenter et tester cette fonction.

Gestion des Dates Null : Mettre à jour clean() pour gérer les cas où start_date ou end_date est None.

Optimiser les Requêtes : Ajouter select_related dans get_commentaires() et get_evenements().

Documenter le JSON details : Si utilisé, expliquer sa structure.

Tester les Cas Limites :

prevus_crif = 0 et prevus_mp = 0 → taux_saturation doit gérer la division par zéro.

nombre_candidats = 0 → taux_transformation doit retourner 0.0.



 # --------------------------------------------------------
 # Autres verifs formations
 # --------------------------------------------------------

🔎 À vérifier dans les modèles liés
Modèle Centre
Vérifications :

✅ Formation.centre est bien un ForeignKey vers Centre.

✅ related_name="formations" permet d'accéder aux formations depuis un centre.

❓ À confirmer : Le champ objectif_mensuel_jury existe-t-il dans Centre ? Est-il utilisé dans SuiviJury ?

✅ __str__() est défini pour l'affichage dans l'admin et les logs.

📍 Modèle TypeOffre
Vérifications :

✅ Formation.type_offre est bien un ForeignKey.

✅ related_name="formations" fonctionne.

❓ À vérifier : Si get_badge_html() est utilisé dans l'admin, il doit être implémenté dans TypeOffre.

✅ couleur est utilisé pour le frontend (badges, filtres).

📍 Modèle Statut
Vérifications :

✅ Formation.statut est bien un ForeignKey.

✅ related_name="formations" est correct.

❗ Problème potentiel : Si statut.couleur est None, get_status_color() utilise get_default_color(). Cette fonction doit exister et gérer tous les cas.

✅ __str__() est nécessaire pour l'affichage.

2. Vérification des Relations ManyToMany
📍 Modèle Partenaire
Vérifications :

✅ Formation.partenaires est un ManyToManyField avec related_name="formations".

❗ À vérifier : Le __str__() de Partenaire doit être explicite (ex: return self.nom).

✅ Les partenaires sont bien sérialisés dans to_serializable_dict().

3. Vérification des Modèles Liés (Commentaires, Événements, Documents)
📍 Modèle Commentaire
Vérifications :

✅ related_name="commentaires" dans Commentaire.formation.

✅ saturation et contenu sont des champs obligatoires ? Si oui, null=False.

❗ Optimisation : Ajouter un index sur created_at pour order_by('-created_at').

✅ La méthode add_commentaire() met à jour dernier_commentaire.

📍 Modèle Evenement
Vérifications :

✅ related_name="evenements" dans Evenement.formation.

❗ À confirmer : Evenement.AUTRE doit être défini (ex: class Evenement.Types).

✅ add_evenement() incrémente correctement nombre_evenements.

📍 Modèle Document (si existant)
Vérifications :

✅ related_name="documents" dans Document.formation.

❗ Optimisation : Ajouter un index sur formation_id si les requêtes sont fréquentes.

4. Vérification de l'Historique
📍 Modèle HistoriqueFormation
Vérifications :

✅ formation = ForeignKey(null=False) → OK si on ne logue que les formations.

✅ created_by est hérité de BaseModel.

❗ À vérifier : Le champ details (JSON) est-il utilisé ? Si oui, documenter son format.

✅ Les modifications sont bien tracées dans save() via HistoriqueFormation.