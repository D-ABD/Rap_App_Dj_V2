cp .env.local .env        
python manage.py runserver




git add .
git commit -m "
-Réparation de "Candidat
-Ajout de CVTheque
- Dernière version stable de l'app avant prod
- Faire les tests en prod
"
git push origin main



faire un readmepour chaque model 



je pense que j'ai des erreurs de logique dans mon model. 
Je souhaite que tu verifies mes champs et méthodes.
Voici les champs à verifier plus précisément et leurs methodes vérifie aussi tout le reste :
    nombre_places_ouvertes 
    nombre_prescriptions 
    nb_inscrits 
    nb_presents 
    nb_absents 
    nb_adhesions 

Voici la logique souhaité: 

- Nombre de places ouvertes, nombre de presriptions et nombre d'adhésion, ne sont utiles que pour l'information collective

- nombre_places_ouvertes = Nombre de place que je propose pour que les prescripteurs inscrivent des candidats

- nombre_prescriptions = Le nombre de candidats inscrits par les prescripteurs

- nb_adhesions = Nombre de candidats qui adhrent au dispositif, lors de l'information collective.

Nombre d'inscrits est pour les ateliers (1,2,3,4,5,6,) et nombre

- nb_inscrits 
    nb_presents 
    nb_absents 




En clair, j'ai un objectif annuel,par exemple, accueilir 400 personnes sur le département. Chaque centre du département a donc ses objectifs, ouvre des places aux informations collectives et le prescripteur nous envois des candidats.Ici, je souhaite calculer le taux de prescriptions par rapport aux places ouvertes. Je souhaite aussi suivre le nombre de places ouvertes au total vs le nombre de prescriptions.

 Parfois toutes les places sont occupées et parfois non. C'est pourquoi je compte les présents et les absents. Cequi fait quej'ai besoin aussi du taux de présence aux informations collectives et suivre le nombre d'inscrits, présents et absents.
 
 Parmi les présents, ils adherent ou pas au dispositif. J'ai besoin de compter parmi lenombre de présent, le nombre qui adherent. Ce qui permet de calculer le taux d'adhésion.
 
 Parmi ceux qui adherent, je les inscrits à des atelier. J'ai besoin de compter le nombre d'inscrits aux atelier, présents et absents et avoir le taux deprésence aux ateliers

 L'atelier 1 est le début du parcours. J'ai besoin de creer une methode pour voir la difference entre le début de parcours et la fin pour voir si je perds des personnes. 

 Est ce correct si je fais :
 - ajouter nombre_presents information collective= nombre de personnes présentesà    l'information collective

- Modifier nb_present en nb_present_atelier= nombre de personnes presentes à l'atelier

- ajouter nombre_absent_information collective= nombre de personnes absents à l'information collective

- Modifier nb_absent en nb_absent_atelier= nombre de personnes absent à l'atelier