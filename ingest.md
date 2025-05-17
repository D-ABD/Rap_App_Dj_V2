Directory structure:
└── d-abd-rap_app_dj_v2.git/
    ├── README.md
    ├── __init__.py
    ├── backup.sql
    ├── commandes.md
    ├── formation.js
    ├── manage.py
    ├── requirements.txt
    ├── tests_shell.md
    ├── formations/
    │   └── documents/
    ├── logs/
    ├── media/
    │   └── formations/
    │       └── documents/
    │           ├── autre/
    │           │   ├── 2/
    │           │   └── 37/
    │           └── pdf/
    │               ├── 11/
    │               ├── 12/
    │               ├── 13/
    │               ├── 15/
    │               ├── 17/
    │               ├── 18/
    │               ├── 19/
    │               ├── 2/
    │               ├── 20/
    │               ├── 22/
    │               ├── 24/
    │               ├── 25/
    │               ├── 26/
    │               ├── 4/
    │               ├── 5/
    │               ├── 6/
    │               ├── 7/
    │               └── 9/
    ├── rap_app/
    │   ├── __init__.py
    │   ├── apps.py
    │   ├── middleware.py
    │   ├── urls.py
    │   ├── .DS_Store
    │   ├── __pycache__/
    │   ├── admin/
    │   │   ├── __init__.py
    │   │   ├── centres_admin.py
    │   │   ├── commentaires_admin.py
    │   │   ├── documents_admin.py
    │   │   ├── evenements_admin.py
    │   │   ├── formations_admin.py
    │   │   ├── partenaires_admin.py
    │   │   ├── prepa_admin.py
    │   │   ├── prospection_admin.py
    │   │   ├── statuts_admin.py
    │   │   ├── types_offre_admin.py
    │   │   ├── user_admin.py
    │   │   └── __pycache__/
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── api_urls.py
    │   │   ├── paginations.py
    │   │   ├── permissions.py
    │   │   ├── __pycache__/
    │   │   ├── serializers/
    │   │   │   ├── base_serializers.md
    │   │   │   ├── centres_serializers.py
    │   │   │   ├── commentaires_serializers.py
    │   │   │   ├── documents_serializers.py
    │   │   │   ├── evenements_serializers.py
    │   │   │   ├── formations_serializers.py
    │   │   │   ├── login_logout_serializers.py
    │   │   │   ├── logs_serializers.py
    │   │   │   ├── partenaires_serializers.py
    │   │   │   ├── prepacomp_serializers.py
    │   │   │   ├── prospection_serializers.py
    │   │   │   ├── rapports_serializers.py
    │   │   │   ├── statut_serializers.py
    │   │   │   ├── types_offre_serializers.py
    │   │   │   ├── user_profil_serializers.py
    │   │   │   ├── vae_jury_serializers.py
    │   │   │   └── __pycache__/
    │   │   └── viewsets/
    │   │       ├── auth_viewset.py
    │   │       ├── base_viewsets.py
    │   │       ├── centres_viewsets.py
    │   │       ├── commentaires_viewsets.py
    │   │       ├── documents_viewsets.py
    │   │       ├── evenements_viewsets.py
    │   │       ├── formations_viewsets.py
    │   │       ├── login_logout_viewset.py
    │   │       ├── logs_viewsets.py
    │   │       ├── partenaires_viewsets.py
    │   │       ├── prepacomp_viewsets.py
    │   │       ├── prospection_viewsets.py
    │   │       ├── rapports_viewsets.py
    │   │       ├── statut_viewsets.py
    │   │       ├── temporaire_viewset.py
    │   │       ├── types_offre_viewsets.py
    │   │       ├── user_viewsets.py
    │   │       ├── vae_jury_viewsets.py
    │   │       └── __pycache__/
    │   ├── forms/
    │   │   └── __init__.py
    │   ├── management/
    │   │   ├── __init__.py
    │   │   ├── __pycache__/
    │   │   └── commands/
    │   │       ├── __init__.py
    │   │       ├── verifie_modeles.py
    │   │       └── verifie_modeles_lies.py
    │   ├── migrations/
    │   │   ├── 0001_initial.py
    │   │   ├── 0002_alter_logutilisateur_options_and_more.py
    │   │   ├── __init__.py
    │   │   └── __pycache__/
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── centres.py
    │   │   ├── commentaires.py
    │   │   ├── custom_user.py
    │   │   ├── documents.py
    │   │   ├── evenements.py
    │   │   ├── formations.py
    │   │   ├── logs.py
    │   │   ├── models_test.py
    │   │   ├── partenaires.py
    │   │   ├── prepacomp.py
    │   │   ├── prospection.py
    │   │   ├── rapports.py
    │   │   ├── statut.py
    │   │   ├── types_offre.py
    │   │   ├── vae_jury.py
    │   │   └── __pycache__/
    │   ├── services/
    │   │   └── generateur_rapports.py
    │   ├── signals/
    │   │   ├── __init__.py
    │   │   ├── centres_signals.py
    │   │   ├── commentaire_signals.py
    │   │   ├── documents_signals.py
    │   │   ├── evenements_signals.py
    │   │   ├── formations_signals.py
    │   │   ├── logs_signals.py
    │   │   ├── partenaires_signals.py
    │   │   ├── prepacomp_signals.py
    │   │   ├── prospections_signals.py
    │   │   ├── rapports_signals.py
    │   │   ├── statut_signals.py
    │   │   ├── types_offres_signals.py
    │   │   ├── vae_jury_signals.py
    │   │   └── __pycache__/
    │   ├── static/
    │   │   ├── __init__.py
    │   │   ├── css/
    │   │   │   └── formation.css
    │   │   ├── images/
    │   │   └── js/
    │   │       └── formation.js
    │   ├── templates/
    │   │   ├── base.html
    │   │   ├── home.html
    │   │   └── .DS_Store
    │   ├── templatetags/
    │   │   ├── __init__.py
    │   │   └── __pycache__/
    │   ├── tests/
    │   │   ├── __init__.py
    │   │   ├── __pycache__/
    │   │   ├── tests_models/
    │   │   │   ├── __init__.py
    │   │   │   ├── setup_base_tests.py
    │   │   │   ├── test_centres.py
    │   │   │   ├── tests_base.py
    │   │   │   ├── tests_commentaires.py
    │   │   │   ├── tests_documents.py
    │   │   │   ├── tests_evenements.py
    │   │   │   ├── tests_formations.py
    │   │   │   ├── tests_logs.py
    │   │   │   ├── tests_partenaires.py
    │   │   │   ├── tests_prepacomp.py
    │   │   │   ├── tests_prospection.py
    │   │   │   ├── tests_rapports.py
    │   │   │   ├── tests_statut.py
    │   │   │   ├── tests_types_offre.py
    │   │   │   ├── tests_user.py
    │   │   │   ├── tests_vae_jury.py
    │   │   │   └── __pycache__/
    │   │   ├── tests_serializers/
    │   │   │   ├── __init__.py
    │   │   │   ├── tests_centres_serializers.py
    │   │   │   ├── tests_commentaires_serializers.py
    │   │   │   ├── tests_documents_vserializers.py
    │   │   │   ├── tests_evenements_serializers.py
    │   │   │   ├── tests_formations_serializers.py
    │   │   │   ├── tests_login_logout_serializers.py
    │   │   │   ├── tests_logs_serializers.py
    │   │   │   ├── tests_me_serializers.py
    │   │   │   ├── tests_partenaires_serializers.py
    │   │   │   ├── tests_prepacomp_serializers.py
    │   │   │   ├── tests_prospection_serializers.py
    │   │   │   ├── tests_rapports_serializers.py
    │   │   │   ├── tests_statut_serializers.py
    │   │   │   ├── tests_temporaire_serializers.py
    │   │   │   ├── tests_types_offre_serializers.py
    │   │   │   ├── tests_user_profile_serializers.py
    │   │   │   ├── tests_vae_jury_serializers.py
    │   │   │   └── __pycache__/
    │   │   └── tests_viewsets/
    │   │       ├── __init__.py
    │   │       ├── tests_centres_viewsets.py
    │   │       ├── tests_commentaires_viewsets.py
    │   │       ├── tests_company_viewsets.py
    │   │       ├── tests_documents_viewsets.py
    │   │       ├── tests_evenements_viewsets.py
    │   │       ├── tests_formations_viewsets.py
    │   │       ├── tests_login_logout_viewset.py
    │   │       ├── tests_logs_viewsets.py
    │   │       ├── tests_me_viewset.py
    │   │       ├── tests_partenaires_viewsets.py
    │   │       ├── tests_prepacomp_viewsets.py
    │   │       ├── tests_prospection_viewsets.py
    │   │       ├── tests_rapports_viewsets.py
    │   │       ├── tests_statut_viewsets.py
    │   │       ├── tests_temporaire_viewset.py
    │   │       ├── tests_types_offre_viewsets.py
    │   │       ├── tests_user_profile_viewsets.py
    │   │       ├── tests_vae_jury_viewsets.py
    │   │       └── __pycache__/
    │   ├── utils/
    │   │   └── logging_utils.py
    │   └── views/
    │       ├── __init__.py
    │       ├── base_views.py
    │       ├── centres_views.py
    │       ├── commentaires_views.py
    │       ├── dashboard_views.py
    │       ├── documents_views.py
    │       ├── evenements_views.py
    │       ├── formations_views.py
    │       ├── historique_formation_views.py
    │       ├── home_views.py
    │       ├── log_views.py
    │       ├── parametres_views.py
    │       ├── partenaires_views.py
    │       ├── prepa_views.py
    │       ├── prospection_views.py
    │       ├── rapport_views.py
    │       ├── statuts_views.py
    │       ├── types_offre_views.py
    │       ├── users_views.py
    │       ├── vae_jury_views.py
    │       └── __pycache__/
    ├── rap_app_project/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── __pycache__/
    └── staticfiles/
        ├── __init__.py
        ├── admin/
        │   ├── css/
        │   │   ├── autocomplete.css
        │   │   ├── base.css
        │   │   ├── changelists.css
        │   │   ├── dark_mode.css
        │   │   ├── dashboard.css
        │   │   ├── forms.css
        │   │   ├── login.css
        │   │   ├── nav_sidebar.css
        │   │   ├── responsive.css
        │   │   ├── responsive_rtl.css
        │   │   ├── rtl.css
        │   │   ├── widgets.css
        │   │   └── vendor/
        │   │       └── select2/
        │   │           ├── LICENSE-SELECT2.md
        │   │           └── select2.css
        │   ├── img/
        │   │   ├── LICENSE
        │   │   ├── README.txt
        │   │   └── gis/
        │   └── js/
        │       ├── actions.js
        │       ├── autocomplete.js
        │       ├── calendar.js
        │       ├── cancel.js
        │       ├── change_form.js
        │       ├── collapse.js
        │       ├── core.js
        │       ├── filters.js
        │       ├── inlines.js
        │       ├── jquery.init.js
        │       ├── nav_sidebar.js
        │       ├── popup_response.js
        │       ├── prepopulate.js
        │       ├── prepopulate_init.js
        │       ├── SelectBox.js
        │       ├── SelectFilter2.js
        │       ├── theme.js
        │       ├── urlify.js
        │       ├── admin/
        │       │   ├── DateTimeShortcuts.js
        │       │   └── RelatedObjectLookups.js
        │       └── vendor/
        │           ├── jquery/
        │           │   ├── jquery.js
        │           │   └── LICENSE.txt
        │           ├── select2/
        │           │   ├── LICENSE.md
        │           │   ├── select2.full.js
        │           │   └── i18n/
        │           │       ├── af.js
        │           │       ├── ar.js
        │           │       ├── az.js
        │           │       ├── bg.js
        │           │       ├── bn.js
        │           │       ├── bs.js
        │           │       ├── ca.js
        │           │       ├── cs.js
        │           │       ├── da.js
        │           │       ├── de.js
        │           │       ├── dsb.js
        │           │       ├── el.js
        │           │       ├── en.js
        │           │       ├── es.js
        │           │       ├── et.js
        │           │       ├── eu.js
        │           │       ├── fa.js
        │           │       ├── fi.js
        │           │       ├── fr.js
        │           │       ├── gl.js
        │           │       ├── he.js
        │           │       ├── hi.js
        │           │       ├── hr.js
        │           │       ├── hsb.js
        │           │       ├── hu.js
        │           │       ├── hy.js
        │           │       ├── id.js
        │           │       ├── is.js
        │           │       ├── it.js
        │           │       ├── ja.js
        │           │       ├── ka.js
        │           │       ├── km.js
        │           │       ├── ko.js
        │           │       ├── lt.js
        │           │       ├── lv.js
        │           │       ├── mk.js
        │           │       ├── ms.js
        │           │       ├── nb.js
        │           │       ├── ne.js
        │           │       ├── nl.js
        │           │       ├── pl.js
        │           │       ├── ps.js
        │           │       ├── pt-BR.js
        │           │       ├── pt.js
        │           │       ├── ro.js
        │           │       ├── ru.js
        │           │       ├── sk.js
        │           │       ├── sl.js
        │           │       ├── sq.js
        │           │       ├── sr-Cyrl.js
        │           │       ├── sr.js
        │           │       ├── sv.js
        │           │       ├── th.js
        │           │       ├── tk.js
        │           │       ├── tr.js
        │           │       ├── uk.js
        │           │       ├── vi.js
        │           │       ├── zh-CN.js
        │           │       └── zh-TW.js
        │           └── xregexp/
        │               ├── LICENSE.txt
        │               └── xregexp.js
        └── rap_app/
            ├── css/
            │   └── formation.css
            ├── images/
            └── js/
                └── formation.js


Files Content:

(Files content cropped to 300k characters, download full ingest to see more)
================================================
FILE: README.md
================================================
# Rapp_App_Dj# Rap_App_Dj_V2



================================================
FILE: __init__.py
================================================



================================================
FILE: backup.sql
================================================
host -p 5432 -d rap_app_db --verbose > backup.sql 2>&1
pg_dump: last built-in OID is 16383
pg_dump: reading extensions
pg_dump: identifying extension members
pg_dump: reading schemas
pg_dump: reading user-defined tables
pg_dump: reading user-defined functions
pg_dump: reading user-defined types
pg_dump: reading procedural languages
pg_dump: reading user-defined aggregate functions
pg_dump: reading user-defined operators
pg_dump: reading user-defined access methods
pg_dump: reading user-defined operator classes
pg_dump: reading user-defined operator families
pg_dump: reading user-defined text search parsers
pg_dump: reading user-defined text search templates
pg_dump: reading user-defined text search dictionaries
pg_dump: reading user-defined text search configurations
pg_dump: reading user-defined foreign-data wrappers
pg_dump: reading user-defined foreign servers
pg_dump: reading default privileges
pg_dump: reading user-defined collations
pg_dump: reading user-defined conversions
pg_dump: reading type casts
pg_dump: reading transforms
pg_dump: reading table inheritance information
pg_dump: reading event triggers
pg_dump: finding extension tables
pg_dump: finding inheritance relationships
pg_dump: reading column info for interesting tables
pg_dump: finding table check constraints
pg_dump: flagging inherited columns in subtables
pg_dump: reading partitioning data
pg_dump: reading indexes
pg_dump: flagging indexes in partitioned tables
pg_dump: reading extended statistics
pg_dump: reading constraints
pg_dump: reading triggers
pg_dump: reading rewrite rules
pg_dump: reading policies
pg_dump: reading row-level security policies
pg_dump: reading publications
pg_dump: reading publication membership of tables
pg_dump: reading publication membership of schemas
pg_dump: reading subscriptions
pg_dump: reading large objects
pg_dump: reading dependency data
pg_dump: saving encoding = UTF8
pg_dump: saving standard_conforming_strings = on
pg_dump: saving search_path = 
pg_dump: creating TABLE "public.auth_group"
pg_dump: creating SEQUENCE "public.auth_group_id_seq"
pg_dump: creating TABLE "public.auth_group_permissions"
pg_dump: creating SEQUENCE "public.auth_group_permissions_id_seq"
pg_dump: creating TABLE "public.auth_permission"
pg_dump: creating SEQUENCE "public.auth_permission_id_seq"
pg_dump: creating TABLE "public.auth_user"
pg_dump: creating TABLE "public.auth_user_groups"
pg_dump: creating SEQUENCE "public.auth_user_groups_id_seq"
pg_dump: creating SEQUENCE "public.auth_user_id_seq"
pg_dump: creating TABLE "public.auth_user_user_permissions"
pg_dump: creating SEQUENCE "public.auth_user_user_permissions_id_seq"
pg_dump: creating TABLE "public.companies"
pg_dump: creating SEQUENCE "public.companies_id_seq"
pg_dump: creating TABLE "public.django_admin_log"
pg_dump: creating SEQUENCE "public.django_admin_log_id_seq"
pg_dump: creating TABLE "public.django_content_type"
pg_dump: creating SEQUENCE "public.django_content_type_id_seq"
pg_dump: creating TABLE "public.django_migrations"
pg_dump: creating SEQUENCE "public.django_migrations_id_seq"
pg_dump: creating TABLE "public.django_session"
pg_dump: creating TABLE "public.rap_app_centre"
pg_dump: creating SEQUENCE "public.rap_app_centre_id_seq"
pg_dump: creating TABLE "public.rap_app_commentaire"
pg_dump: creating SEQUENCE "public.rap_app_commentaire_id_seq"
pg_dump: creating TABLE "public.rap_app_document"
pg_dump: creating SEQUENCE "public.rap_app_document_id_seq"
pg_dump: creating TABLE "public.rap_app_evenement"
pg_dump: creating SEQUENCE "public.rap_app_evenement_id_seq"
pg_dump: creating TABLE "public.rap_app_formation"
pg_dump: creating SEQUENCE "public.rap_app_formation_id_seq"
pg_dump: creating TABLE "public.rap_app_formation_partenaires"
pg_dump: creating SEQUENCE "public.rap_app_formation_partenaires_id_seq"
pg_dump: creating TABLE "public.rap_app_historiqueformation"
pg_dump: creating SEQUENCE "public.rap_app_historiqueformation_id_seq"
pg_dump: creating TABLE "public.rap_app_historiqueprospection"
pg_dump: creating SEQUENCE "public.rap_app_historiqueprospection_id_seq"
pg_dump: creating TABLE "public.rap_app_historiquestatutvae"
pg_dump: creating SEQUENCE "public.rap_app_historiquestatutvae_id_seq"
pg_dump: creating TABLE "public.rap_app_partenaire"
pg_dump: creating SEQUENCE "public.rap_app_partenaire_id_seq"
pg_dump: creating TABLE "public.rap_app_prepacompglobal"
pg_dump: creating SEQUENCE "public.rap_app_prepacompglobal_id_seq"
pg_dump: creating TABLE "public.rap_app_prospection"
pg_dump: creating SEQUENCE "public.rap_app_prospection_id_seq"
pg_dump: creating TABLE "public.rap_app_rapport"
pg_dump: creating SEQUENCE "public.rap_app_rapport_id_seq"
pg_dump: creating TABLE "public.rap_app_semaine"
pg_dump: creating SEQUENCE "public.rap_app_semaine_id_seq"
pg_dump: creating TABLE "public.rap_app_statut"
pg_dump: creating SEQUENCE "public.rap_app_statut_id_seq"
pg_dump: creating TABLE "public.rap_app_suivijury"
pg_dump: creating SEQUENCE "public.rap_app_suivijury_id_seq"
pg_dump: creating TABLE "public.rap_app_typeoffre"
pg_dump: creating SEQUENCE "public.rap_app_typeoffre_id_seq"
pg_dump: creating TABLE "public.rap_app_vae"
pg_dump: creating SEQUENCE "public.rap_app_vae_id_seq"
pg_dump: processing data for table "public.auth_group"
pg_dump: dumping contents of table "public.auth_group"
pg_dump: processing data for table "public.auth_group_permissions"
pg_dump: dumping contents of table "public.auth_group_permissions"
pg_dump: processing data for table "public.auth_permission"
pg_dump: dumping contents of table "public.auth_permission"
pg_dump: processing data for table "public.auth_user"
pg_dump: dumping contents of table "public.auth_user"
pg_dump: processing data for table "public.auth_user_groups"
pg_dump: dumping contents of table "public.auth_user_groups"
pg_dump: processing data for table "public.auth_user_user_permissions"
pg_dump: dumping contents of table "public.auth_user_user_permissions"
pg_dump: processing data for table "public.companies"
pg_dump: dumping contents of table "public.companies"
pg_dump: processing data for table "public.django_admin_log"
pg_dump: dumping contents of table "public.django_admin_log"
pg_dump: processing data for table "public.django_content_type"
pg_dump: dumping contents of table "public.django_content_type"
pg_dump: processing data for table "public.django_migrations"
pg_dump: dumping contents of table "public.django_migrations"
pg_dump: processing data for table "public.django_session"
pg_dump: dumping contents of table "public.django_session"
pg_dump: processing data for table "public.rap_app_centre"
pg_dump: dumping contents of table "public.rap_app_centre"
pg_dump: processing data for table "public.rap_app_commentaire"
pg_dump: dumping contents of table "public.rap_app_commentaire"
pg_dump: processing data for table "public.rap_app_document"
pg_dump: dumping contents of table "public.rap_app_document"
pg_dump: processing data for table "public.rap_app_evenement"
pg_dump: dumping contents of table "public.rap_app_evenement"
pg_dump: processing data for table "public.rap_app_formation"
pg_dump: dumping contents of table "public.rap_app_formation"
pg_dump: processing data for table "public.rap_app_formation_partenaires"
pg_dump: dumping contents of table "public.rap_app_formation_partenaires"
pg_dump: processing data for table "public.rap_app_historiqueformation"
pg_dump: dumping contents of table "public.rap_app_historiqueformation"
pg_dump: processing data for table "public.rap_app_historiqueprospection"
pg_dump: dumping contents of table "public.rap_app_historiqueprospection"
pg_dump: processing data for table "public.rap_app_historiquestatutvae"
pg_dump: dumping contents of table "public.rap_app_historiquestatutvae"
pg_dump: processing data for table "public.rap_app_partenaire"
pg_dump: dumping contents of table "public.rap_app_partenaire"
pg_dump: processing data for table "public.rap_app_prepacompglobal"
pg_dump: dumping contents of table "public.rap_app_prepacompglobal"
pg_dump: processing data for table "public.rap_app_prospection"
pg_dump: dumping contents of table "public.rap_app_prospection"
pg_dump: processing data for table "public.rap_app_rapport"
pg_dump: dumping contents of table "public.rap_app_rapport"
pg_dump: processing data for table "public.rap_app_semaine"
pg_dump: dumping contents of table "public.rap_app_semaine"
pg_dump: processing data for table "public.rap_app_statut"
pg_dump: dumping contents of table "public.rap_app_statut"
pg_dump: processing data for table "public.rap_app_suivijury"
pg_dump: dumping contents of table "public.rap_app_suivijury"
pg_dump: processing data for table "public.rap_app_typeoffre"
pg_dump: dumping contents of table "public.rap_app_typeoffre"
pg_dump: processing data for table "public.rap_app_vae"
pg_dump: dumping contents of table "public.rap_app_vae"
pg_dump: executing SEQUENCE SET auth_group_id_seq
pg_dump: executing SEQUENCE SET auth_group_permissions_id_seq
pg_dump: executing SEQUENCE SET auth_permission_id_seq
pg_dump: executing SEQUENCE SET auth_user_groups_id_seq
pg_dump: executing SEQUENCE SET auth_user_id_seq
pg_dump: executing SEQUENCE SET auth_user_user_permissions_id_seq
pg_dump: executing SEQUENCE SET companies_id_seq
pg_dump: executing SEQUENCE SET django_admin_log_id_seq
pg_dump: executing SEQUENCE SET django_content_type_id_seq
pg_dump: executing SEQUENCE SET django_migrations_id_seq
pg_dump: executing SEQUENCE SET rap_app_centre_id_seq
pg_dump: executing SEQUENCE SET rap_app_commentaire_id_seq
pg_dump: executing SEQUENCE SET rap_app_document_id_seq
pg_dump: executing SEQUENCE SET rap_app_evenement_id_seq
pg_dump: executing SEQUENCE SET rap_app_formation_id_seq
pg_dump: executing SEQUENCE SET rap_app_formation_partenaires_id_seq
pg_dump: executing SEQUENCE SET rap_app_historiqueformation_id_seq
pg_dump: executing SEQUENCE SET rap_app_historiqueprospection_id_seq
pg_dump: executing SEQUENCE SET rap_app_historiquestatutvae_id_seq
pg_dump: executing SEQUENCE SET rap_app_partenaire_id_seq
pg_dump: executing SEQUENCE SET rap_app_prepacompglobal_id_seq
pg_dump: executing SEQUENCE SET rap_app_prospection_id_seq
pg_dump: executing SEQUENCE SET rap_app_rapport_id_seq
pg_dump: executing SEQUENCE SET rap_app_semaine_id_seq
pg_dump: executing SEQUENCE SET rap_app_statut_id_seq
pg_dump: executing SEQUENCE SET rap_app_suivijury_id_seq
pg_dump: executing SEQUENCE SET rap_app_typeoffre_id_seq
pg_dump: executing SEQUENCE SET rap_app_vae_id_seq
pg_dump: creating CONSTRAINT "public.auth_group auth_group_name_key"
pg_dump: creating CONSTRAINT "public.auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq"
pg_dump: creating CONSTRAINT "public.auth_group_permissions auth_group_permissions_pkey"
pg_dump: creating CONSTRAINT "public.auth_group auth_group_pkey"
pg_dump: creating CONSTRAINT "public.auth_permission auth_permission_content_type_id_codename_01ab375a_uniq"
pg_dump: creating CONSTRAINT "public.auth_permission auth_permission_pkey"
pg_dump: creating CONSTRAINT "public.auth_user_groups auth_user_groups_pkey"
pg_dump: creating CONSTRAINT "public.auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq"
pg_dump: creating CONSTRAINT "public.auth_user auth_user_pkey"
pg_dump: creating CONSTRAINT "public.auth_user_user_permissions auth_user_user_permissions_pkey"
pg_dump: creating CONSTRAINT "public.auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq"
pg_dump: creating CONSTRAINT "public.auth_user auth_user_username_key"
pg_dump: creating CONSTRAINT "public.companies companies_pkey"
pg_dump: creating CONSTRAINT "public.django_admin_log django_admin_log_pkey"
pg_dump: creating CONSTRAINT "public.django_content_type django_content_type_app_label_model_76bd3d3b_uniq"
pg_dump: creating CONSTRAINT "public.django_content_type django_content_type_pkey"
pg_dump: creating CONSTRAINT "public.django_migrations django_migrations_pkey"
pg_dump: creating CONSTRAINT "public.django_session django_session_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_centre rap_app_centre_nom_key"
pg_dump: creating CONSTRAINT "public.rap_app_centre rap_app_centre_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_commentaire rap_app_commentaire_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_document rap_app_document_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_evenement rap_app_evenement_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_formation_partenaires rap_app_formation_parten_formation_id_partenaire__9296cffb_uniq"
pg_dump: creating CONSTRAINT "public.rap_app_formation_partenaires rap_app_formation_partenaires_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_formation rap_app_formation_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_historiqueformation rap_app_historiqueformation_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_historiqueprospection rap_app_historiqueprospection_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_historiquestatutvae rap_app_historiquestatutvae_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_partenaire rap_app_partenaire_nom_key"
pg_dump: creating CONSTRAINT "public.rap_app_partenaire rap_app_partenaire_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_partenaire rap_app_partenaire_slug_key"
pg_dump: creating CONSTRAINT "public.rap_app_prepacompglobal rap_app_prepacompglobal_centre_id_annee_d54ed7f7_uniq"
pg_dump: creating CONSTRAINT "public.rap_app_prepacompglobal rap_app_prepacompglobal_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_prospection rap_app_prospection_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_rapport rap_app_rapport_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_semaine rap_app_semaine_numero_semaine_annee_centre_id_15574399_uniq"
pg_dump: creating CONSTRAINT "public.rap_app_semaine rap_app_semaine_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_statut rap_app_statut_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_suivijury rap_app_suivijury_centre_id_annee_mois_d9c2bc45_uniq"
pg_dump: creating CONSTRAINT "public.rap_app_suivijury rap_app_suivijury_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_typeoffre rap_app_typeoffre_pkey"
pg_dump: creating CONSTRAINT "public.rap_app_vae rap_app_vae_pkey"
pg_dump: creating INDEX "public.auth_group_name_a6ea08ec_like"
pg_dump: creating INDEX "public.auth_group_permissions_group_id_b120cbf9"
pg_dump: creating INDEX "public.auth_group_permissions_permission_id_84c5c92e"
pg_dump: creating INDEX "public.auth_permission_content_type_id_2f476e4b"
pg_dump: creating INDEX "public.auth_user_groups_group_id_97559544"
pg_dump: creating INDEX "public.auth_user_groups_user_id_6a12ed8b"
pg_dump: creating INDEX "public.auth_user_user_permissions_permission_id_1fbb5f2c"
pg_dump: creating INDEX "public.auth_user_user_permissions_user_id_a95ead1b"
pg_dump: creating INDEX "public.auth_user_username_6821ab7c_like"
pg_dump: creating INDEX "public.companies_created_by_id_0ca1dbbf"
pg_dump: creating INDEX "public.company_city_idx"
pg_dump: creating INDEX "public.company_name_idx"
pg_dump: creating INDEX "public.company_sector_idx"
pg_dump: creating INDEX "public.company_zipcode_idx"
pg_dump: creating INDEX "public.django_admin_log_content_type_id_c4bce8eb"
pg_dump: creating INDEX "public.django_admin_log_user_id_c564eba6"
pg_dump: creating INDEX "public.django_session_expire_date_a5c62663"
pg_dump: creating INDEX "public.django_session_session_key_c0390e0f_like"
pg_dump: creating INDEX "public.rap_app_cen_code_po_c9960c_idx"
pg_dump: creating INDEX "public.rap_app_cen_nom_671da5_idx"
pg_dump: creating INDEX "public.rap_app_centre_nom_0ebf6a73_like"
pg_dump: creating INDEX "public.rap_app_com_created_aad49b_idx"
pg_dump: creating INDEX "public.rap_app_com_formati_0c3422_idx"
pg_dump: creating INDEX "public.rap_app_commentaire_formation_id_411b8e35"
pg_dump: creating INDEX "public.rap_app_commentaire_utilisateur_id_5fd836f7"
pg_dump: creating INDEX "public.rap_app_doc_formati_399b58_idx"
pg_dump: creating INDEX "public.rap_app_doc_nom_fic_b4d61d_idx"
pg_dump: creating INDEX "public.rap_app_doc_type_do_ef9a30_idx"
pg_dump: creating INDEX "public.rap_app_document_formation_id_901f20bf"
pg_dump: creating INDEX "public.rap_app_document_nom_fichier_0bf73b42"
pg_dump: creating INDEX "public.rap_app_document_nom_fichier_0bf73b42_like"
pg_dump: creating INDEX "public.rap_app_document_utilisateur_id_3b4930e8"
pg_dump: creating INDEX "public.rap_app_eve_event_d_758395_idx"
pg_dump: creating INDEX "public.rap_app_eve_formati_3e51e7_idx"
pg_dump: creating INDEX "public.rap_app_eve_type_ev_11d24c_idx"
pg_dump: creating INDEX "public.rap_app_evenement_formation_id_9d5bdde6"
pg_dump: creating INDEX "public.rap_app_evenement_type_evenement_c7bc3a20"
pg_dump: creating INDEX "public.rap_app_evenement_type_evenement_c7bc3a20_like"
pg_dump: creating INDEX "public.rap_app_for_end_dat_e7d2c9_idx"
pg_dump: creating INDEX "public.rap_app_for_nom_27c494_idx"
pg_dump: creating INDEX "public.rap_app_for_start_d_4c1834_idx"
pg_dump: creating INDEX "public.rap_app_formation_centre_id_f0f1b26c"
pg_dump: creating INDEX "public.rap_app_formation_partenaires_formation_id_ca802956"
pg_dump: creating INDEX "public.rap_app_formation_partenaires_partenaire_id_a0f47348"
pg_dump: creating INDEX "public.rap_app_formation_statut_id_093f283d"
pg_dump: creating INDEX "public.rap_app_formation_type_offre_id_5c6e76b2"
pg_dump: creating INDEX "public.rap_app_formation_utilisateur_id_c1c28de0"
pg_dump: creating INDEX "public.rap_app_his_date_mo_5b61b9_idx"
pg_dump: creating INDEX "public.rap_app_his_prochai_5f80db_idx"
pg_dump: creating INDEX "public.rap_app_his_prospec_f00db9_idx"
pg_dump: creating INDEX "public.rap_app_historiqueformation_formation_id_82faa1b8"
pg_dump: creating INDEX "public.rap_app_historiqueformation_modifie_par_id_a9f19085"
pg_dump: creating INDEX "public.rap_app_historiqueprospection_modifie_par_id_ba747269"
pg_dump: creating INDEX "public.rap_app_historiqueprospection_prospection_id_67a9f10f"
pg_dump: creating INDEX "public.rap_app_historiquestatutvae_vae_id_36e46d31"
pg_dump: creating INDEX "public.rap_app_par_nom_983061_idx"
pg_dump: creating INDEX "public.rap_app_par_secteur_455cf4_idx"
pg_dump: creating INDEX "public.rap_app_par_slug_09691e_idx"
pg_dump: creating INDEX "public.rap_app_partenaire_nom_2803ee73_like"
pg_dump: creating INDEX "public.rap_app_partenaire_slug_2fe2610a_like"
pg_dump: creating INDEX "public.rap_app_prepacompglobal_centre_id_613695ed"
pg_dump: creating INDEX "public.rap_app_pro_company_bb2e93_idx"
pg_dump: creating INDEX "public.rap_app_pro_date_pr_5d71cf_idx"
pg_dump: creating INDEX "public.rap_app_pro_formati_986a4a_idx"
pg_dump: creating INDEX "public.rap_app_pro_respons_fb7ec5_idx"
pg_dump: creating INDEX "public.rap_app_pro_statut_84d25a_idx"
pg_dump: creating INDEX "public.rap_app_prospection_company_id_e480a03d"
pg_dump: creating INDEX "public.rap_app_prospection_formation_id_0afd22a1"
pg_dump: creating INDEX "public.rap_app_prospection_responsable_id_4ae46661"
pg_dump: creating INDEX "public.rap_app_rapport_centre_id_7aeb7f3c"
pg_dump: creating INDEX "public.rap_app_rapport_formation_id_b5903e24"
pg_dump: creating INDEX "public.rap_app_rapport_statut_id_19a3a41a"
pg_dump: creating INDEX "public.rap_app_rapport_type_offre_id_82c16da7"
pg_dump: creating INDEX "public.rap_app_rapport_utilisateur_id_6112cdc0"
pg_dump: creating INDEX "public.rap_app_semaine_centre_id_89920e81"
pg_dump: creating INDEX "public.rap_app_sui_centre__1773ec_idx"
pg_dump: creating INDEX "public.rap_app_suivijury_centre_id_097a587b"
pg_dump: creating INDEX "public.rap_app_typ_autre_76e40c_idx"
pg_dump: creating INDEX "public.rap_app_typ_nom_d4cbe0_idx"
pg_dump: creating INDEX "public.rap_app_vae_centre__309bad_idx"
pg_dump: creating INDEX "public.rap_app_vae_centre_id_7fde3aaf"
pg_dump: creating INDEX "public.rap_app_vae_date_cr_61a6f5_idx"
pg_dump: creating INDEX "public.unique_autre_non_null"
pg_dump: creating FK CONSTRAINT "public.auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm"
pg_dump: creating FK CONSTRAINT "public.auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id"
pg_dump: creating FK CONSTRAINT "public.auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co"
pg_dump: creating FK CONSTRAINT "public.auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id"
pg_dump: creating FK CONSTRAINT "public.auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm"
pg_dump: creating FK CONSTRAINT "public.auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.companies companies_created_by_id_0ca1dbbf_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co"
pg_dump: creating FK CONSTRAINT "public.django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_commentaire rap_app_commentaire_formation_id_411b8e35_fk_rap_app_f"
pg_dump: creating FK CONSTRAINT "public.rap_app_commentaire rap_app_commentaire_utilisateur_id_5fd836f7_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_document rap_app_document_formation_id_901f20bf_fk_rap_app_formation_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_document rap_app_document_utilisateur_id_3b4930e8_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_evenement rap_app_evenement_formation_id_9d5bdde6_fk_rap_app_formation_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_formation rap_app_formation_centre_id_f0f1b26c_fk_rap_app_centre_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_formation_partenaires rap_app_formation_pa_formation_id_ca802956_fk_rap_app_f"
pg_dump: creating FK CONSTRAINT "public.rap_app_formation_partenaires rap_app_formation_pa_partenaire_id_a0f47348_fk_rap_app_p"
pg_dump: creating FK CONSTRAINT "public.rap_app_formation rap_app_formation_statut_id_093f283d_fk_rap_app_statut_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_formation rap_app_formation_type_offre_id_5c6e76b2_fk_rap_app_t"
pg_dump: creating FK CONSTRAINT "public.rap_app_formation rap_app_formation_utilisateur_id_c1c28de0_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_historiqueformation rap_app_historiquefo_formation_id_82faa1b8_fk_rap_app_f"
pg_dump: creating FK CONSTRAINT "public.rap_app_historiqueformation rap_app_historiquefo_modifie_par_id_a9f19085_fk_auth_user"
pg_dump: creating FK CONSTRAINT "public.rap_app_historiqueprospection rap_app_historiquepr_modifie_par_id_ba747269_fk_auth_user"
pg_dump: creating FK CONSTRAINT "public.rap_app_historiqueprospection rap_app_historiquepr_prospection_id_67a9f10f_fk_rap_app_p"
pg_dump: creating FK CONSTRAINT "public.rap_app_historiquestatutvae rap_app_historiquestatutvae_vae_id_36e46d31_fk_rap_app_vae_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_prepacompglobal rap_app_prepacompglobal_centre_id_613695ed_fk_rap_app_centre_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_prospection rap_app_prospection_company_id_e480a03d_fk_companies_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_prospection rap_app_prospection_formation_id_0afd22a1_fk_rap_app_f"
pg_dump: creating FK CONSTRAINT "public.rap_app_prospection rap_app_prospection_responsable_id_4ae46661_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_rapport rap_app_rapport_centre_id_7aeb7f3c_fk_rap_app_centre_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_rapport rap_app_rapport_formation_id_b5903e24_fk_rap_app_formation_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_rapport rap_app_rapport_statut_id_19a3a41a_fk_rap_app_statut_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_rapport rap_app_rapport_type_offre_id_82c16da7_fk_rap_app_typeoffre_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_rapport rap_app_rapport_utilisateur_id_6112cdc0_fk_auth_user_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_semaine rap_app_semaine_centre_id_89920e81_fk_rap_app_centre_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_suivijury rap_app_suivijury_centre_id_097a587b_fk_rap_app_centre_id"
pg_dump: creating FK CONSTRAINT "public.rap_app_vae rap_app_vae_centre_id_7fde3aaf_fk_rap_app_centre_id"



# Remplace les valeurs par celles de TON projet Supabase
PGPASSWORD="@Marielle1012" \
psql -h vvfebufvsaneevlujzlc.supabase.co \
     -U postgres \
     -d rap_app_db \
     -p 5432 \
     < backup.sql


================================================
FILE: commandes.md
================================================
# ========================================================
# GESTION DE PROJET DJANGO - CHEAT SHEET (Python3/Pip3)
# ========================================================

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
git commit -m "Amélioration models, signals, serialyze_dict"   
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




================================================
FILE: formation.js
================================================



================================================
FILE: manage.py
================================================
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rap_app_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()



================================================
FILE: requirements.txt
================================================
asgiref==3.8.1
attrs==25.1.0
chardet==5.2.0
coverage==7.7.1
Django==4.2.7
django-cors-headers==4.7.0
django-filter==25.1
django-guardian==2.4.0
djangorestframework==3.14.0
djangorestframework_simplejwt==5.5.0
drf-spectacular==0.28.0
et_xmlfile==2.0.0
inflection==0.5.1
iniconfig==2.1.0
jsonschema==4.23.0
jsonschema-specifications==2024.10.1
lxml==5.3.1
numpy==2.2.3
openpyxl==3.1.5
packaging==24.2
pandas==2.2.3
pillow==11.1.0
pluggy==1.5.0
psycopg2-binary==2.9.10
PyJWT==2.9.0
pytest==8.3.5
pytest-django==4.10.0
python-dateutil==2.9.0.post0
python-decouple==3.8
python-docx==1.1.2
python-dotenv==1.0.1
python-magic==0.4.27
pytz==2025.1
PyYAML==6.0.2
referencing==0.36.2
reportlab==4.3.1
rpds-py==0.23.1
six==1.17.0
sqlparse==0.5.3
typing_extensions==4.12.2
tzdata==2025.1
uritemplate==4.1.1



================================================
FILE: tests_shell.md
================================================

























================================================
FILE: rap_app/__init__.py
================================================



================================================
FILE: rap_app/apps.py
================================================
# apps.py

from django.apps import AppConfig


class RapAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rap_app'


    def ready(self):
        import rap_app.signals.centres_signals
        import rap_app.signals.commentaire_signals
        import rap_app.signals.documents_signals
        import rap_app.signals.evenements_signals
        import rap_app.signals.formations_signals
        import rap_app.signals.rapports_signals
        import rap_app.signals.prospections_signals
        import rap_app.signals.prepacomp_signals
        import rap_app.signals.logs_signals  
        import rap_app.signals.statut_signals



================================================
FILE: rap_app/middleware.py
================================================
# myapp/middleware.py
import threading

_thread_locals = threading.local()

def get_current_user():
    """Récupère l'utilisateur courant stocké dans le thread local."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware qui stocke l'utilisateur actuel dans le thread local
    pour qu'il soit accessible depuis n'importe où dans le code.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Stocke l'utilisateur dans le thread local
        _thread_locals.user = request.user if hasattr(request, 'user') else None
        
        response = self.get_response(request)
        
        # Nettoie après la réponse pour éviter les fuites de mémoire
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
            
        return response


================================================
FILE: rap_app/urls.py
================================================
from django.urls import path

from .views import home_views






urlpatterns = [
    # Page d'accueil
    path('', home_views.home, name='home'),

    # Rapports
    # Liste des rapports

    # USERS


    # Dashboard


    # Centres de formation
    # Statuts des formations
    # Types d'offres

    # Commentaires

    # Documents
    
    # Partenaires
    # Événements
    
    # Formations
        # Historique des Formations

    # Paramètres

    # Prospections

 # Prepa_Comp


    # ---- Semaines ----


    # ---- Global annuel ----
    
    # Suivis des jurys    
    # VAE
        
    # Historique des statuts VAE
    
    
    ]




================================================
FILE: rap_app/.DS_Store
================================================
[Non-text file]



================================================
FILE: rap_app/admin/__init__.py
================================================
"""
Importe les classes admin pour l'interface d'administration Django.
L'importation des classes admin enregistre automatiquement les modèles avec admin.site.
"""




================================================
FILE: rap_app/admin/centres_admin.py
================================================



================================================
FILE: rap_app/admin/commentaires_admin.py
================================================



================================================
FILE: rap_app/admin/documents_admin.py
================================================



================================================
FILE: rap_app/admin/evenements_admin.py
================================================



================================================
FILE: rap_app/admin/formations_admin.py
================================================



================================================
FILE: rap_app/admin/partenaires_admin.py
================================================



================================================
FILE: rap_app/admin/prepa_admin.py
================================================



================================================
FILE: rap_app/admin/prospection_admin.py
================================================



================================================
FILE: rap_app/admin/statuts_admin.py
================================================



================================================
FILE: rap_app/admin/types_offre_admin.py
================================================



================================================
FILE: rap_app/admin/user_admin.py
================================================




================================================
FILE: rap_app/api/__init__.py
================================================



================================================
FILE: rap_app/api/api_urls.py
================================================
from django.urls import path
from rest_framework.routers import DefaultRouter

from .viewsets.auth_viewset import EmailTokenObtainPairView
from .viewsets.login_logout_viewset import LoginAPIView, LogoutAPIView
from .viewsets.temporaire_viewset import test_token_view
from rest_framework_simplejwt.views import TokenRefreshView

# ViewSets
# ✅ Ajout pour permettre reverse('api:...') dans les tests
app_name = "api"

router = DefaultRouter()

urlpatterns = router.urls + [
    # Authentification
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),

    # Infos utilisateur et test
    path('test-token/', test_token_view),
]



================================================
FILE: rap_app/api/paginations.py
================================================
# rap_app/api/paginations.py

from rest_framework.pagination import PageNumberPagination

class RapAppPagination(PageNumberPagination):
    """
    Pagination personnalisée pour l'API Rap App.
    
    - page_size : nombre d'éléments par défaut par page (10)
    - page_size_query_param : permet au client de demander plus/moins d'éléments avec ?page_size=
    - max_page_size : limite maximale autorisée pour éviter les abus (100)
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100



================================================
FILE: rap_app/api/permissions.py
================================================
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperAdminOnly(BasePermission):
    """
    Autorise uniquement les superadmins à accéder à cette vue.
    """
    message = "Accès réservé aux superadmins uniquement."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.profile.role == 'superadmin'
        )


class IsAdmin(BasePermission):
    """
    Autorise uniquement les administrateurs (staff, admin, superadmin) à accéder à cette vue.
    """
    message = "Accès réservé aux membres du staff, admins ou superadmins."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.profile.role in ['staff', 'admin', 'superadmin']
        )


class ReadWriteAdminReadStaff(BasePermission):
    """
    Lecture : autorisée pour staff, admin, superadmin.
    Écriture : réservée à admin et superadmin uniquement.
    """
    message = "Lecture autorisée pour le staff. Modifications réservées aux admins ou superadmins."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        role = getattr(user.profile, 'role', None)

        if request.method in SAFE_METHODS:
            if role in ['staff', 'admin', 'superadmin']:
                return True
            self.message = "Lecture réservée au staff, admins ou superadmins."
            return False

        if role in ['admin', 'superadmin']:
            return True

        self.message = "Seuls les admins ou superadmins peuvent modifier cette ressource."
        return False


class IsStaffOrAbove(BasePermission):
    """
    Autorise uniquement le staff, les admins ou les superadmins à accéder à la vue.
    """
    message = "Accès réservé au staff, aux admins ou aux superadmins."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.profile.role in ['staff', 'admin', 'superadmin']
        )


class ReadOnlyOrAdmin(BasePermission):
    """
    Tout le monde peut lire (GET, HEAD, OPTIONS), seuls les admins ou superadmins peuvent modifier.
    """
    message = "Lecture publique. Modifications réservées aux admins ou superadmins."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user.is_authenticated and
            request.user.profile.role in ['admin', 'superadmin']
        )
class IsOwnerOrSuperAdmin(BasePermission):
    """
    Autorise l'accès si l'utilisateur est le propriétaire OU superadmin.
    """
    message = "Vous ne pouvez accéder qu'à vos propres données, sauf si vous êtes superadmin."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        if getattr(user.profile, 'role', '') == 'superadmin':
            return True

        return getattr(obj, 'user', None) == user or getattr(obj, 'owner', None) == user

class IsOwnerOrStaffOrAbove(BasePermission): 
    """
    Autorise l'accès si l'utilisateur est le propriétaire OU staff/admin/superadmin.
    """
    message = "Accès réservé au propriétaire ou aux membres du staff, admin ou superadmin."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            self.message = "Authentification requise."
            return False

        if getattr(user.profile, 'role', '') in ['staff', 'admin', 'superadmin']:
            return True

        return getattr(obj, 'user', None) == user or getattr(obj, 'owner', None) == user




================================================
FILE: rap_app/api/serializers/base_serializers.md
================================================



================================================
FILE: rap_app/api/serializers/centres_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/commentaires_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/documents_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/evenements_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/formations_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/login_logout_serializers.py
================================================
# Myevol_app/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                username=email, password=password)
            if not user:
                msg = 'Impossible de se connecter avec ces identifiants.'
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = 'Veuillez entrer votre email et mot de passe.'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


================================================
FILE: rap_app/api/serializers/logs_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/partenaires_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/prepacomp_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/prospection_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/rapports_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/statut_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/types_offre_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/user_profil_serializers.py
================================================



================================================
FILE: rap_app/api/serializers/vae_jury_serializers.py
================================================




================================================
FILE: rap_app/api/viewsets/auth_viewset.py
================================================
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



from django.contrib.auth import get_user_model

User = get_user_model()

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD  # ← utilise le champ email

    def validate(self, attrs):
        attrs['username'] = attrs.get('email')  # ✅ remplace "username" par "email"
        return super().validate(attrs)

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer



================================================
FILE: rap_app/api/viewsets/base_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/centres_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/commentaires_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/documents_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/evenements_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/formations_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/login_logout_viewset.py
================================================
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout

from drf_spectacular.utils import extend_schema

from ..serializers.login_logout_serializers import LoginSerializer, UserSerializer


@extend_schema(
    tags=["Authentification"],
    summary="Connexion",
    description="""
    Permet à un utilisateur de se connecter et de recevoir un token d'authentification.

    ✅ Accès public (non authentifié).
    🔐 Le token est requis ensuite pour les appels protégés.
    """,
    request=LoginSerializer,
    responses={200: UserSerializer}
)
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentification"],
    summary="Déconnexion",
    description="""
    Permet à un utilisateur connecté de se déconnecter et d'invalider son token d'authentification.

    🔒 Requiert un token actif dans l’en-tête Authorization.
    """,
    responses={200: {"type": "object", "properties": {
        "detail": {"type": "string", "example": "Déconnexion réussie."}
    }}}
)
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass

        logout(request)
        return Response({"detail": "Déconnexion réussie."}, status=status.HTTP_200_OK)



================================================
FILE: rap_app/api/viewsets/logs_viewsets.py
================================================
# IsSuperAdminOnly

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, DateTimeFilter

from ..serializers.logs_serializers import LogUtilisateurSerializer
from ...models.logs import LogUtilisateur
from ..permissions import IsSuperAdminOnly


class LogUtilisateurFilter(FilterSet):
    """
    Filtres personnalisés pour les logs :
    - date_min : logs après cette date
    - date_max : logs avant cette date
    """

    date_min = DateTimeFilter(field_name="date", lookup_expr="gte")
    date_max = DateTimeFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = LogUtilisateur
        fields = ['utilisateur', 'modele', 'action']


@extend_schema(
    tags=["Logs"],
    summary="Historique des actions utilisateur",
    description="""
        Affiche les logs détaillés des actions effectuées par les utilisateurs.

        🔐 Accessible uniquement aux `superadmins`.

        Fonctionnalités :
        - Recherche : action, modèle, utilisateur
        - Filtres : utilisateur, modèle, action, date_min, date_max
        - Tri : par date ou modèle
    """
)
class LogUtilisateurViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ReadOnly pour consulter les logs utilisateurs.

    🔒 Permission : superadmin uniquement
    ✅ Filtres et recherche avancés
    """

    queryset = LogUtilisateur.objects.select_related('utilisateur').all()
    serializer_class = LogUtilisateurSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LogUtilisateurFilter
    search_fields = ['utilisateur__username', 'utilisateur__email', 'action', 'modele']
    ordering_fields = ['date', 'modele']
    ordering = ['-date']



================================================
FILE: rap_app/api/viewsets/partenaires_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/prepacomp_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/prospection_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/rapports_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/statut_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/temporaire_viewset.py
================================================
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema


@extend_schema(
    tags=["🔐 Authentification"],
    summary="Vérifier la validité du token et le rôle",
    description="""
        Cette vue permet de vérifier si un token d’authentification (JWT ou DRF Token) est valide,
        et retourne les informations du compte utilisateur connecté, y compris son rôle.

        🔒 Requiert un token d’authentification valide.
    """,
    responses={
        200: {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "user_id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string"},
                "is_staff": {"type": "boolean"},
                "is_superuser": {"type": "boolean"},
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_token_view(request):
    """
    ✅ Teste si le token est valide et renvoie les informations utilisateur, y compris le rôle.
    """
    user = request.user
    role = getattr(user.profile, 'role', 'inconnu')  # évite une erreur si profil absent

    return Response({
        'success': True,
        'message': 'Token valide ✅',
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': role,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })



================================================
FILE: rap_app/api/viewsets/types_offre_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/user_viewsets.py
================================================



================================================
FILE: rap_app/api/viewsets/vae_jury_viewsets.py
================================================




================================================
FILE: rap_app/forms/__init__.py
================================================



================================================
FILE: rap_app/management/__init__.py
================================================




================================================
FILE: rap_app/management/commands/__init__.py
================================================



================================================
FILE: rap_app/management/commands/verifie_modeles.py
================================================
# rap_app_project/rap_app/management/commands/verifie_modeles.py
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
import inspect
from django.db.models.fields import Field
from django.utils.termcolors import colorize
import re
import importlib
import sys
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Vérifie que tous les modèles respectent les standards de qualité'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Limiter la vérification à une application spécifique'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Limiter la vérification à un modèle spécifique'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tenter de corriger automatiquement certains problèmes'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Exporter les résultats dans un fichier'
        )

    def handle(self, *args, **options):
        self.app_filter = options.get('app')
        self.model_filter = options.get('model')
        self.fix_mode = options.get('fix', False)
        self.export_file = options.get('export')
        
        # Initialiser le rapport
        self.report = []
        self.issues_count = 0
        self.models_checked = 0
        
        # Identifier les modèles à vérifier
        all_models = self._get_models_to_check()
        
        self.stdout.write(f"Vérification de {len(all_models)} modèles...")
        
        # Vérifier chaque modèle
        for model in all_models:
            self.models_checked += 1
            model_name = model.__name__
            app_label = model._meta.app_label
            
            # Afficher l'en-tête du modèle
            header = f"\n{'='*60}\nVérification du modèle {app_label}.{model_name}\n{'='*60}"
            self.stdout.write(self.style.MIGRATE_HEADING(header))
            self.report.append(header)
            
            # Effectuer toutes les vérifications
            self._check_model(model)
        
        # Résumé
        summary = f"\n\n{'='*60}\nRÉSUMÉ\n{'='*60}\n"
        summary += f"Modèles vérifiés: {self.models_checked}\n"
        summary += f"Problèmes identifiés: {self.issues_count}\n"
        
        self.stdout.write(self.style.SUCCESS(summary))
        self.report.append(summary)
        
        # Export du rapport si demandé
        if self.export_file:
            with open(self.export_file, 'w') as f:
                f.write('\n'.join(self.report))
            self.stdout.write(f"Rapport exporté vers {self.export_file}")
    
    def _get_models_to_check(self):
        """Récupère la liste des modèles à vérifier selon les filtres appliqués."""
        if self.model_filter and self.app_filter:
            # Un modèle spécifique dans une app spécifique
            try:
                return [apps.get_model(self.app_filter, self.model_filter)]
            except LookupError:
                self.stderr.write(f"Modèle {self.app_filter}.{self.model_filter} introuvable")
                sys.exit(1)
        elif self.app_filter:
            # Tous les modèles d'une app spécifique
            return [m for m in apps.get_models() if m._meta.app_label == self.app_filter]
        elif self.model_filter:
            # Un modèle spécifique dans toutes les apps
            models_found = []
            for app_config in apps.get_app_configs():
                try:
                    models_found.append(apps.get_model(app_config.label, self.model_filter))
                except LookupError:
                    pass
            if not models_found:
                self.stderr.write(f"Modèle {self.model_filter} introuvable dans aucune app")
                sys.exit(1)
            return models_found
        else:
            # Tous les modèles de toutes les apps (sauf celles exclues)
            excluded_apps = ['admin', 'auth', 'contenttypes', 'sessions', 'staticfiles', 'messages']
            return [m for m in apps.get_models() if m._meta.app_label not in excluded_apps]
    
    def _check_model(self, model):
        """Effectue toutes les vérifications sur un modèle donné."""
        # Vérifier la présence des méthodes essentielles
        self._check_essential_methods(model)
        
        # Vérifier les docstrings
        self._check_docstrings(model)
        
        # Vérifier les champs et les méta-options
        self._check_fields_and_meta(model)
        
        # Vérifier les duplications avec BaseModel
        self._check_base_model_duplication(model)
        
        # Vérifier la présence de to_serializable_dict
        self._check_serialization(model)
        
        # Vérifier la gestion des erreurs
        self._check_error_handling(model)
        
        # Vérifier les indexations
        self._check_indexes(model)
        
        # Vérifier les valeurs par défaut
        self._check_default_values(model)
        
        # Vérifier les validations
        self._check_validations(model)
    
    def _add_issue(self, message, severity='warning', model=None, fix_suggestion=None):
        """Ajoute un problème au rapport."""
        self.issues_count += 1
        
        if severity == 'error':
            style = self.style.ERROR
            prefix = '❌ ERREUR:'
        elif severity == 'warning':
            style = self.style.WARNING
            prefix = '⚠️ AVERTISSEMENT:'
        else:
            style = self.style.NOTICE
            prefix = 'ℹ️ INFO:'
        
        formatted_message = f"{prefix} {message}"
        if fix_suggestion:
            formatted_message += f"\n   👉 Suggestion: {fix_suggestion}"
        
        self.stdout.write(style(formatted_message))
        self.report.append(formatted_message)
    
    def _add_success(self, message):
        """Ajoute un succès au rapport."""
        formatted_message = f"✅ {message}"
        self.stdout.write(self.style.SUCCESS(formatted_message))
        self.report.append(formatted_message)
    
    def _check_essential_methods(self, model):
        """Vérifie la présence des méthodes essentielles."""
        essential_methods = {
            "__str__": "Méthode __str__() pour représentation lisible",
            "clean": "Méthode clean() pour validations",
            "": "Méthode () pour navigation"
        }
        
        for method_name, description in essential_methods.items():
            has_method = hasattr(model, method_name) and callable(getattr(model, method_name))
            if has_method:
                self._add_success(f"{description} présente")
            else:
                self._add_issue(
                    f"{description} manquante",
                    severity='warning',
                    model=model,
                    fix_suggestion=f"Ajouter une méthode {method_name}() au modèle {model.__name__}"
                )
    
    def _check_docstrings(self, model):
        """Vérifie la présence et la qualité des docstrings."""
        # Vérifier le docstring de la classe
        has_docstring = model.__doc__ is not None
        has_good_docstring = has_docstring and len(model.__doc__.strip()) > 10
        
        if has_good_docstring:
            self._add_success("Docstring de classe présente et complète")
        elif has_docstring:
            self._add_issue(
                "Docstring de classe trop courte",
                severity='warning',
                model=model,
                fix_suggestion="Ajouter une description complète du modèle et de ses attributs"
            )
        else:
            self._add_issue(
                "Docstring de classe manquante",
                severity='error',
                model=model,
                fix_suggestion="Ajouter une docstring décrivant le modèle et ses attributs"
            )
        
        # Vérifier les docstrings des méthodes
        methods_checked = 0
        methods_with_docstring = 0
        
        for name, method in inspect.getmembers(model, predicate=inspect.isfunction):
            # Ignorer les méthodes privées sauf __init__
            if name.startswith('_') and name != '__init__':
                continue
            
            methods_checked += 1
            has_method_doc = method.__doc__ is not None and len(method.__doc__.strip()) > 5
            
            if has_method_doc:
                methods_with_docstring += 1
            else:
                self._add_issue(
                    f"Docstring manquante pour la méthode {name}()",
                    severity='warning',
                    model=model,
                    fix_suggestion=f"Ajouter une docstring à la méthode {name}()"
                )
        
        if methods_checked > 0 and methods_with_docstring == methods_checked:
            self._add_success(f"Toutes les méthodes ({methods_checked}) ont des docstrings")
    
    def _check_fields_and_meta(self, model):
        """Vérifie les attributs des champs et les méta-options."""
        # Vérifier verbose_name et help_text sur les champs
        missing_verbose = []
        missing_help_text = []
        
        for field in model._meta.fields:
            # Ignorer les champs primaires et les champs qui pourrait être hérités
            if field.primary_key or field.name in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                continue
                
            if not hasattr(field, 'verbose_name') or field.verbose_name == field.name:
                missing_verbose.append(field.name)
            
            if not hasattr(field, 'help_text') or not field.help_text:
                missing_help_text.append(field.name)
        
        if missing_verbose:
            self._add_issue(
                f"Champs sans verbose_name: {', '.join(missing_verbose)}",
                severity='warning',
                model=model,
                fix_suggestion="Ajouter un verbose_name explicite à tous les champs"
            )
        else:
            self._add_success("Tous les champs ont un verbose_name")
            
        if missing_help_text:
            self._add_issue(
                f"Champs sans help_text: {', '.join(missing_help_text)}",
                severity='warning',
                model=model,
                fix_suggestion="Ajouter un help_text à tous les champs"
            )
        else:
            self._add_success("Tous les champs ont un help_text")
        
        # Vérifier les meta options
        if not hasattr(model, 'Meta'):
            self._add_issue(
                "Classe Meta manquante",
                severity='warning',
                model=model,
                fix_suggestion="Ajouter une classe Meta avec verbose_name et ordering"
            )
        else:
            meta = model._meta
            
            # Vérifier verbose_name
            if not meta.verbose_name or meta.verbose_name == meta.model_name:
                self._add_issue(
                    "verbose_name manquant ou générique dans Meta",
                    severity='warning',
                    model=model,
                    fix_suggestion="Ajouter un verbose_name explicite dans la classe Meta"
                )
            else:
                self._add_success("verbose_name défini dans Meta")
            
            # Vérifier ordering
            if not meta.ordering:
                self._add_issue(
                    "ordering manquant dans Meta",
                    severity='warning',
                    model=model,
                    fix_suggestion="Ajouter un ordering par défaut dans la classe Meta"
                )
            else:
                self._add_success(f"ordering défini dans Meta: {meta.ordering}")
    
    def _check_base_model_duplication(self, model):
        """Vérifie si le modèle hérite de BaseModel et s'il duplique des champs."""
        # Récupérer la classe BaseModel si elle existe
        try:
            # Essayer différents chemins possibles pour BaseModel
            base_model_paths = [
                f"{model._meta.app_label}.models.base.BaseModel",
                f"{model._meta.app_label}.base.BaseModel",
                "base.BaseModel",
                "models.base.BaseModel"
            ]
            
            BaseModel = None
            for path in base_model_paths:
                try:
                    module_path, class_name = path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    BaseModel = getattr(module, class_name)
                    break
                except (ImportError, AttributeError, ValueError):
                    continue
            
            if not BaseModel:
                self._add_issue(
                    "Impossible de trouver la classe BaseModel",
                    severity='notice',
                    model=model
                )
                return
            
            # Vérifier si le modèle hérite de BaseModel
            if issubclass(model, BaseModel) and model != BaseModel:
                base_fields = [f.name for f in BaseModel._meta.get_fields()]
                duplicated = []
                
                for field in model._meta.get_fields():
                    if field.name in base_fields and not field.primary_key and not field.is_relation:
                        duplicated.append(field.name)
                
                if duplicated:
                    self._add_issue(
                        f"Champs dupliqués de BaseModel: {', '.join(duplicated)}",
                        severity='error',
                        model=model,
                        fix_suggestion=f"Supprimer les champs {', '.join(duplicated)} du modèle car ils sont déjà définis dans BaseModel"
                    )
                else:
                    self._add_success("Pas de duplication avec BaseModel")
            else:
                # Si le modèle n'hérite pas de BaseModel, suggérer de le faire
                self._add_issue(
                    "Le modèle n'hérite pas de BaseModel",
                    severity='notice',
                    model=model,
                    fix_suggestion="Envisager d'hériter de BaseModel pour avoir created_at, updated_at, etc."
                )
        
        except Exception as e:
            self._add_issue(
                f"Erreur lors de la vérification de BaseModel: {str(e)}",
                severity='notice',
                model=model
            )
    
    def _check_serialization(self, model):
        """Vérifie la présence de méthodes de sérialisation."""
        has_serializable = hasattr(model, 'to_serializable_dict') and callable(getattr(model, 'to_serializable_dict'))
        
        if has_serializable:
            # Vérifier si la méthode retourne bien un dictionnaire
            method = getattr(model, 'to_serializable_dict')
            signature = inspect.signature(method)
            
            if 'return' in method.__annotations__ and method.__annotations__['return'] == dict:
                self._add_success("Méthode to_serializable_dict() bien typée")
            else:
                self._add_issue(
                    "Méthode to_serializable_dict() sans annotation de type de retour",
                    severity='warning',
                    model=model,
                    fix_suggestion="Ajouter l'annotation -> dict à la méthode"
                )
        else:
            self._add_issue(
                "Méthode to_serializable_dict() manquante",
                severity='error',
                model=model,
                fix_suggestion="Ajouter une méthode to_serializable_dict() qui convertit l'instance en dictionnaire pour l'API"
            )
    
    def _check_error_handling(self, model):
        """Vérifie la gestion des erreurs dans le modèle."""
        # Vérifier si clean() existe et lève des ValidationError
        if hasattr(model, 'clean') and callable(getattr(model, 'clean')):
            clean_method = getattr(model, 'clean')
            source = inspect.getsource(clean_method)
            
            if 'ValidationError' in source and 'raise ValidationError' in source:
                self._add_success("La méthode clean() lève des ValidationError")
            else:
                self._add_issue(
                    "La méthode clean() ne semble pas lever d'exceptions ValidationError",
                    severity='warning',
                    model=model,
                    fix_suggestion="Ajouter des validations avec raise ValidationError() dans clean()"
                )
        
        # Vérifier si save() gère les exceptions
        if hasattr(model, 'save') and callable(getattr(model, 'save')):
            save_method = getattr(model, 'save')
            source = inspect.getsource(save_method)
            
            if 'try' in source and 'except' in source:
                self._add_success("La méthode save() gère les exceptions")
            else:
                self._add_issue(
                    "La méthode save() ne semble pas gérer les exceptions",
                    severity='notice',
                    model=model,
                    fix_suggestion="Envisager d'ajouter un bloc try/except dans save()"
                )
    
    def _check_indexes(self, model):
        """Vérifie la présence d'indexes sur les champs importants."""
        meta = model._meta
        
        # Vérifier si des indexes sont définis
        indexes_defined = False
        
        # Vérifier les indexes dans Meta.indexes
        if hasattr(meta, 'indexes') and meta.indexes:
            indexes_defined = True
            self._add_success(f"{len(meta.indexes)} index(s) défini(s) dans Meta")
        
        # Vérifier les indexes automatiques (db_index=True)
        indexed_fields = []
        for field in meta.fields:
            if getattr(field, 'db_index', False):
                indexed_fields.append(field.name)
        
        if indexed_fields:
            indexes_defined = True
            self._add_success(f"Champs avec db_index=True: {', '.join(indexed_fields)}")
        
        # Si aucun index n'est défini, suggérer d'en ajouter
        if not indexes_defined:
            # Identifier les champs qui pourraient bénéficier d'un index
            potential_indexes = []
            
            for field in meta.fields:
                name = field.name
                # Les champs de date, les FK, les champs avec 'id' sont des candidats
                if isinstance(field, models.DateField) or isinstance(field, models.ForeignKey) or 'id' in name:
                    potential_indexes.append(name)
            
            if potential_indexes:
                fields_str = ', '.join(potential_indexes)
                self._add_issue(
                    "Aucun index défini",
                    severity='warning',
                    model=model,
                    fix_suggestion=f"Envisager d'ajouter des indexes sur: {fields_str}"
                )
            else:
                self._add_issue(
                    "Aucun index défini",
                    severity='notice',
                    model=model,
                    fix_suggestion="Ajouter des indexes pour les champs souvent utilisés en filtrage"
                )
    
    def _check_default_values(self, model):
        """Vérifie que les champs numériques ont des valeurs par défaut."""
        numeric_fields_without_default = []
        
        for field in model._meta.fields:
            # Vérifier seulement les champs numériques qui ne sont pas des clés primaires
            if isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)) and not field.primary_key:
                # Si le champ peut être null, il n'a pas besoin de default
                if not field.null and not field.has_default():
                    numeric_fields_without_default.append(field.name)
        
        if numeric_fields_without_default:
            self._add_issue(
                f"Champs numériques sans valeur par défaut: {', '.join(numeric_fields_without_default)}",
                severity='warning',
                model=model,
                fix_suggestion="Ajouter default=0 ou une autre valeur appropriée aux champs numériques"
            )
        else:
            self._add_success("Tous les champs numériques ont une valeur par défaut ou peuvent être null")
    
    def _check_validations(self, model):
        """Vérifie la présence de validations dans le modèle."""
        # Vérifier les validations sur les champs numériques (min/max)
        numeric_fields_without_validation = []
        
        for field in model._meta.fields:
            if isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)):
                has_validation = hasattr(field, 'validators') and len(field.validators) > 0
                if not has_validation:
                    numeric_fields_without_validation.append(field.name)
        
        if numeric_fields_without_validation:
            self._add_issue(
                f"Champs numériques sans validation (min/max): {', '.join(numeric_fields_without_validation)}",
                severity='notice',
                model=model,
                fix_suggestion="Ajouter des validators comme MinValueValidator/MaxValueValidator"
            )
        else:
            self._add_success("Tous les champs numériques ont des validations ou n'en ont pas besoin")
        
        # Vérifier la présence de méthodes de validation (clean/full_clean)
        if not hasattr(model, 'clean') or not callable(getattr(model, 'clean')):
            self._add_issue(
                "Méthode clean() manquante pour les validations",
                severity='warning',
                model=model,
                fix_suggestion="Ajouter une méthode clean() pour valider les contraintes entre champs"
            ) 


================================================
FILE: rap_app/management/commands/verifie_modeles_lies.py
================================================
import inspect
import sys
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import RegexValidator
from inspect import getmembers, getsource, ismethod
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Vérifie dynamiquement les modèles selon les bonnes pratiques (DRF, admin, API, frontend...)"


    def _filter_model(self, model, app_filter, model_filter):
        label = model._meta.app_label
        name = model.__name__
        if label.startswith('django') or label in {'admin', 'auth', 'contenttypes', 'sessions'}:
            return False
        if app_filter and label != app_filter:
            return False
        if model_filter and name != model_filter:
            return False
        return True

    def _check_model_structure(self, model, issues):
        base_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
        missing = [f for f in base_fields if not hasattr(model, f)]
        if missing:
            issues["critical"].append(f"Champs BaseModel manquants: {', '.join(missing)}")

        if not model._meta.verbose_name:
            issues["warning"].append("Meta.verbose_name manquant")
        if not hasattr(model, '__str__') or model.__str__ == models.Model.__str__:
            issues["warning"].append("__str__() manquant")
        if not getattr(model._meta, 'ordering', None):
            issues["warning"].append("Meta.ordering manquant")
        if not hasattr(model, 'save') or model.save.__qualname__ == 'Model.save':
            issues["warning"].append("Méthode save() non personnalisée")

    def _check_field_consistency(self, model, issues):
        inherits_base = any(base.__name__ == 'BaseModel' for base in model.__mro__)
        for field in model._meta.get_fields():
            if isinstance(field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)):
                if field.model != model:
                    continue
                if inherits_base and field.name in ['created_by', 'updated_by']:
                    continue
                related_name = getattr(field, 'related_name', None)
                if not related_name or related_name == '+' or ('%(class)s' in str(related_name)):
                    issues["warning"].append(f"Champ relationnel '{field.name}' sans related_name explicite")
                if not getattr(field, 'verbose_name', None):
                    issues["warning"].append(f"Champ '{field.name}' sans verbose_name")
            if isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
                if field.name == 'id' and getattr(field, 'primary_key', False):
                    continue
                if not field.has_default() and not field.null:
                    issues["warning"].append(f"Champ numérique '{field.name}' sans valeur par défaut explicite")

    def _check_data_integrity(self, model, issues):
        if not hasattr(model, 'clean') or model.clean == models.Model.clean:
            issues["warning"].append("Pas de méthode clean() pour validation")
        if hasattr(model, 'save'):
            source = str(model.save.__code__.co_consts)
            if 'full_clean' not in source:
                issues["info"].append("save() n'appelle pas full_clean()")
            if 'transaction.atomic' not in source:
                issues["info"].append("save() n'utilise pas transaction.atomic")
            if 'Historique' in source and 'transaction.atomic' not in source:
                issues["critical"].append("Historique sans transaction.atomic")

    def _check_business_logic(self, model, issues):
        properties = [n for n, o in getmembers(model, lambda o: isinstance(o, property))]
        if not properties:
            issues["info"].append("Aucune propriété calculée trouvée")
        methods = [m for m, _ in getmembers(model, ismethod) if m.startswith('get_') and m not in ['', 'get_FOO_display']]
        if not methods:
            issues["info"].append("Aucune méthode get_*() métier trouvée")

    def _check_api_compatibility(self, model, issues):
        if not any(hasattr(model, m) for m in ['to_serializable_dict', 'to_dict', 'serialize', 'to_json']):
            issues["warning"].append("Pas de méthode to_serializable_dict() ou équivalent")
        if not hasattr(model, ''):
            issues["warning"].append("Pas de méthode () définie")

    def _check_indexation_performance(self, model, issues):
        indexes = getattr(model._meta, 'indexes', [])
        if not indexes:
            issues["warning"].append("Aucun index défini dans Meta.indexes")
        if model._default_manager.__class__.__name__ == 'Manager':
            issues["info"].append("Pas de manager personnalisé")

    def _check_logger_usage(self, model, issues):
        if hasattr(model, 'save'):
            try:
                src = getsource(model.save)
                if 'logger.' not in src:
                    issues["warning"].append("save() n'utilise pas le logger")
                elif 'logger.info' not in src and 'logger.debug' not in src:
                    issues["info"].append("logger utilisé sans niveau info/debug explicite")
            except Exception:
                issues["info"].append("Impossible de lire la source de save() pour logger")

    def _check_model_constants(self, model, issues):
        constants = {
            'TypeOffre': ['CRIF', 'ALTERNANCE', 'POEC', 'POEI', 'AUTRE', 'COULEURS_PAR_DEFAUT'],
            'VAE': ['STATUT_CHOICES', 'STATUTS_EN_COURS', 'STATUTS_TERMINES'],
            'Rapport': ['TYPE_OCCUPATION', 'TYPE_CENTRE', 'PERIODE_MENSUEL', 'FORMAT_PDF']
        }
        expected = constants.get(model.__name__, [])
        missing = [c for c in expected if not hasattr(model, c)]
        if missing:
            issues["critical"].append(f"{model.__name__}: constantes manquantes: {', '.join(missing)}")

    def _check_signals_usage(self, model, issues):
        if hasattr(model, '__module__'):
            module = model.__module__
            try:
                source = inspect.getsource(sys.modules[module])
                patterns = ['@receiver', 'post_save.connect', 'pre_save.connect', 'post_delete.connect', 'pre_delete.connect']
                if not any(p in source for p in patterns):
                    issues["warning"].append("Pas de signaux détectés dans le module")
            except Exception:
                issues["info"].append("Impossible de vérifier les signaux du module")

    def _check_state_methods(self, model, issues):
        state_methods = {
            'VAE': ['is_en_cours', 'is_terminee', 'dernier_changement_statut'],
            'Formation': ['is_a_recruter'],
            'Evenement': ['get_temporal_status']
        }
        expected = state_methods.get(model.__name__, [])
        missing = [m for m in expected if not hasattr(model, m)]
        if missing:
            issues["warning"].append(f"{model.__name__}: méthodes d'état manquantes: {', '.join(missing)}")


    def _check_formation_specific(self, model, issues, show_ok):
        """Contrôles spécifiques pour le modèle Formation"""
        required_props = ['total_places', 'total_inscrits', 'taux_saturation', 'taux_transformation', 'places_disponibles']
        missing = [p for p in required_props if not hasattr(model, p)]
        if missing:
            issues["critical"].append(f"Formation: propriétés métier manquantes: {', '.join(missing)}")
        elif show_ok:
            issues["info"].append("Formation: toutes les propriétés métier requises sont présentes")

        if not hasattr(model, 'to_serializable_dict'):
            issues["critical"].append("Formation: méthode to_serializable_dict() manquante")

        for method_name in ['add_commentaire', 'add_evenement', 'add_document']:
            if not hasattr(model, method_name):
                issues["warning"].append(f"Formation: méthode {method_name}() manquante")

    def _check_vae_specific(self, model, issues, show_ok):
        """Contrôles spécifiques pour le modèle VAE"""
        required_props = ['reference', 'duree_jours', 'is_en_cours']
        missing = [p for p in required_props if not hasattr(model, p)]
        if missing:
            issues["critical"].append(f"VAE: propriétés requises manquantes: {', '.join(missing)}")

        lists_required = ['STATUTS_EN_COURS', 'STATUTS_TERMINES']
        for l in lists_required:
            if not hasattr(model, l):
                issues["warning"].append(f"VAE: liste de statut manquante: {l}")

        for method in ['is_terminee', 'dernier_changement_statut']:
            if not hasattr(model, method):
                issues["warning"].append(f"VAE: méthode {method}() manquante")

        if show_ok:
            issues["info"].append("VAE: vérifications spécifiques exécutées")



    def _check_suivijury_specific(self, model, issues, show_ok):
        if not hasattr(model, 'pourcentage_mensuel'):
            issues["critical"].append("SuiviJury: propriété 'pourcentage_mensuel' manquante")
        required_fields = ['objectif_jury', 'jurys_realises']
        for field in required_fields:
            if not hasattr(model, field):
                issues["critical"].append(f"SuiviJury: champ obligatoire '{field}' manquant")
        for method in ['get_objectif_auto', 'get_pourcentage_atteinte', 'ecart']:
            if not hasattr(model, method):
                issues["warning"].append(f"SuiviJury: méthode '{method}' manquante")

    def _check_partenaire_specific(self, model, issues, show_ok):
        required_fields = ['nom', 'type', 'slug']
        for field in required_fields:
            if not hasattr(model, field):
                issues["critical"].append(f"Partenaire: champ '{field}' manquant")
        for method in ['get_full_address', 'get_contact_info', 'has_contact_info']:
            if not hasattr(model, method):
                issues["warning"].append(f"Partenaire: méthode utilitaire '{method}' manquante")

    def _check_centre_specific(self, model, issues, show_ok):
        for field in ['nom', 'code_postal']:
            if not hasattr(model, field):
                issues["critical"].append(f"Centre: champ '{field}' manquant")
        if hasattr(model, 'code_postal'):
            field_obj = model._meta.get_field('code_postal')
            if not any(isinstance(v, RegexValidator) for v in getattr(field_obj, 'validators', [])):
                issues["warning"].append("Centre: champ 'code_postal' sans RegexValidator")

    def _check_commentaire_specific(self, model, issues, show_ok):
        for champ in ['saturation', 'contenu', 'created_by']:
            if not hasattr(model, champ):
                issues["critical"].append(f"Commentaire: champ '{champ}' manquant")
        for method in ['get_all_commentaires', 'get_recent_commentaires']:
            if not hasattr(model, method):
                issues["warning"].append(f"Commentaire: méthode '{method}' manquante")


    def _check_document_specific(self, model, issues, show_ok):
        required_fields = ['nom_fichier', 'fichier', 'type_document']
        for field in required_fields:
            if not hasattr(model, field):
                issues["critical"].append(f"Document: champ requis '{field}' manquant")
        if not hasattr(model, 'formation'):
            issues["warning"].append("Document: relation 'formation' attendue")

    def _check_evenement_specific(self, model, issues, show_ok):
        for champ in ['type_evenement', 'event_date']:
            if not hasattr(model, champ):
                issues["critical"].append(f"Evenement: champ requis '{champ}' manquant")
        if not hasattr(model, 'formation'):
            issues["warning"].append("Evenement: relation 'formation' attendue")
        for prop in ['status_label', 'status_color']:
            if not hasattr(model, prop):
                issues["warning"].append(f"Evenement: propriété '{prop}' manquante")

    def _check_prospection_specific(self, model, issues, show_ok):
        for champ in ['contact', 'statut', 'entreprise']:
            if not hasattr(model, champ):
                issues["critical"].append(f"Prospection: champ requis '{champ}' manquant")
        for rel in ['partenaire', 'formation']:
            if not hasattr(model, rel):
                issues["critical"].append(f"Prospection: relation '{rel}' manquante")
        for field in ['motif', 'objectif']:
            if not hasattr(model, field):
                issues["warning"].append(f"Prospection: champ d'état '{field}' manquant")


    def _check_historique_prospection(self, model, issues, show_ok):
        required_fields = ['ancien_statut', 'nouveau_statut', 'date_modification']
        for field in required_fields:
            if not hasattr(model, field):
                issues["critical"].append(f"HistoriqueProspection: champ '{field}' manquant")
        if not hasattr(model, 'prospection'):
            issues["critical"].append("HistoriqueProspection: relation 'prospection' manquante")

    def _check_prepacomp_specific(self, model, issues, show_ok):
        for prop in ['taux_transformation', 'taux_adhesion']:
            if not hasattr(model, prop):
                issues["critical"].append(f"PrepaCompGlobal: propriété '{prop}' manquante")
        for field in ['objectif_annuel_prepa', 'objectif_hebdomadaire_prepa', 'objectif_annuel_jury', 'objectif_mensuel_jury']:
            if not hasattr(model, field):
                issues["critical"].append(f"PrepaCompGlobal: champ d'objectif '{field}' manquant")
        for method in ['taux_objectif_annee', 'objectif_annuel_global', 'objectif_hebdo_global', 'objectifs_par_centre', 'stats_par_mois']:
            if not hasattr(model, method):
                issues["info"].append(f"PrepaCompGlobal: méthode statistique '{method}' manquante")


    def _check_model_specific(self, model, issues, show_ok=False):
        """Appelle les vérifications spécifiques en fonction du modèle"""
        model_name = model.__name__

        specific_checks = {
            'Formation': self._check_formation_specific,
            'VAE': self._check_vae_specific,
            'SuiviJury': self._check_suivijury_specific,
            'Partenaire': self._check_partenaire_specific,
            'Centre': self._check_centre_specific,
            'Commentaire': self._check_commentaire_specific,
            'Document': self._check_document_specific,
            'Evenement': self._check_evenement_specific,
            'Prospection': self._check_prospection_specific,
            'HistoriqueProspection': self._check_historique_prospection,
            'PrepaCompGlobal': self._check_prepacomp_specific,
            'Rapport': self._check_rapport_specific,
            'Statut': self._check_statut_specific,
            'TypeOffre': self._check_typeoffre_specific,
            'LogUtilisateur': self._check_logutilisateur_specific,
            'HistoriqueFormation': self._check_historiqueformation_specific,
        }

        if model_name in specific_checks:
            specific_checks[model_name](model, issues, show_ok)


    def _check_rapport_specific(self, model, issues, show_ok):
                required_fields = ['nom', 'periode', 'date_debut', 'date_fin', 'format', 'donnees', 'type_rapport']
                for field in required_fields:
                    if not hasattr(model, field):
                        issues["critical"].append(f"Rapport: champ essentiel '{field}' manquant")
                        
    def _check_statut_specific(self, model, issues, show_ok):
                if not hasattr(model, 'couleur'):
                    issues["warning"].append("Statut: champ 'couleur' manquant")
                for const in ['NON_DEFINI', 'RECRUTEMENT_EN_COURS', 'AUTRE']:
                    if not hasattr(model, const):
                        issues["critical"].append(f"Statut: constante '{const}' manquante")
                if not hasattr(model, 'get_badge_html'):
                    issues["warning"].append("Statut: méthode 'get_badge_html()' manquante")


    def _check_typeoffre_specific(self, model, issues, show_ok):
                if not hasattr(model, 'couleur'):
                    issues["warning"].append("TypeOffre: champ 'couleur' manquant")
                for const in ['CRIF', 'ALTERNANCE', 'POEC', 'POEI', 'AUTRE']:
                    if not hasattr(model, const):
                        issues["critical"].append(f"TypeOffre: constante '{const}' manquante")
                if not hasattr(model, 'get_badge_html'):
                    issues["info"].append("TypeOffre: méthode 'get_badge_html()' manquante")
                for method in ['is_personnalise', 'calculer_couleur_texte', 'assign_default_color']:
                    if not hasattr(model, method):
                        issues["warning"].append(f"TypeOffre: méthode '{method}' manquante")


    def _check_logutilisateur_specific(self, model, issues, show_ok):
                for champ in ['action', 'date', 'utilisateur', 'object_id']:
                    if not hasattr(model, champ):
                        issues["critical"].append(f"LogUtilisateur: champ '{champ}' manquant")
                if not hasattr(model, 'content_object'):
                    issues["critical"].append("LogUtilisateur: champ GenericForeignKey 'content_object' manquant")
                if not hasattr(model, 'log_action'):
                    issues["warning"].append("LogUtilisateur: méthode 'log_action()' manquante")

    def _check_historiqueformation_specific(self, model, issues, show_ok):
                for champ in ['champ_modifie', 'ancienne_valeur', 'nouvelle_valeur']:
                    if not hasattr(model, champ):
                        issues["critical"].append(f"HistoriqueFormation: champ '{champ}' manquant")
                if not hasattr(model, 'details'):
                    issues["warning"].append("HistoriqueFormation: champ JSONField 'details' manquant")
            
    
 
    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, help="Filtrer une app spécifique")
        parser.add_argument('--model', type=str, help="Filtrer un modèle spécifique")
        parser.add_argument('--verbose', action='store_true', help='Afficher plus de détails')
        parser.add_argument('--show-ok', action='store_true', help='Afficher les vérifications OK')
        parser.add_argument('--export-json', type=str, help='Exporter les résultats JSON dans un fichier')

    def handle(self, *args, **options):
        import json
        from pathlib import Path

        app_filter = options.get('app')
        model_filter = options.get('model')
        verbose = options.get('verbose')
        show_ok = options.get('show_ok')
        export_json = options.get('export_json')

        self.stdout.write(self.style.SUCCESS("🔍 Vérification des modèles...") + "\n")

        models_to_check = [m for m in apps.get_models() if self._filter_model(m, app_filter, model_filter)]

        total = len(models_to_check)
        conformes = 0
        resume = []

        for model in models_to_check:
            issues = {"critical": [], "warning": [], "info": []}
            model_name = model.__name__
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n📦 {model_name} ({model._meta.app_label})"))

            self._check_model_structure(model, issues)
            self._check_field_consistency(model, issues)
            self._check_data_integrity(model, issues)
            self._check_business_logic(model, issues)
            self._check_api_compatibility(model, issues)
            self._check_indexation_performance(model, issues)
            self._check_model_specific(model, issues, show_ok)
            self._check_logger_usage(model, issues)
            self._check_model_constants(model, issues)
            self._check_signals_usage(model, issues)
            self._check_state_methods(model, issues)

            has_crit = bool(issues["critical"])
            has_warn = bool(issues["warning"])
            has_info = bool(issues["info"])

            resume.append({
                "model": model_name,
                "app": model._meta.app_label,
                "critical": issues["critical"],
                "warning": issues["warning"],
                "info": issues["info"] if verbose else []
            })

            for msg in issues["critical"]:
                self.stdout.write(self.style.ERROR(f"   ❌ {msg}"))
            for msg in issues["warning"]:
                self.stdout.write(self.style.WARNING(f"   ⚠️  {msg}"))
            if verbose and has_info:
                for msg in issues["info"]:
                    self.stdout.write(self.style.NOTICE(f"   ℹ️  {msg}"))

            if not has_crit and not has_warn:
                self.stdout.write(self.style.SUCCESS("   ✅ Modèle conforme."))
                conformes += 1

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"📊 Résumé: {conformes}/{total} modèles conformes"))

        non_conformes = [r for r in resume if r['critical'] or r['warning']]
        if non_conformes:
            self.stdout.write("\n📌 Modèles avec problèmes:")
            for r in non_conformes:
                self.stdout.write(f" - {r['model']} ({r['app']}): ❌ {len(r['critical'])} critiques, ⚠️  {len(r['warning'])} avertissements")

        if export_json:
            export_path = Path(export_json).resolve()
            with export_path.open('w', encoding='utf-8') as f:
                json.dump(resume, f, indent=2, ensure_ascii=False)
            self.stdout.write(self.style.SUCCESS(f"\n💾 Résultats exportés vers: {export_path}"))
 


================================================
FILE: rap_app/migrations/0001_initial.py
================================================
# Generated by Django 4.2.7 on 2025-05-10 08:08

from decimal import Decimal
from django.conf import settings
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.datetime
import django.utils.timezone
import rap_app.models.documents
import rap_app.models.prepacomp


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(error_messages={'unique': 'Un utilisateur avec cette adresse email existe déjà.'}, help_text='Adresse email utilisée pour la connexion', max_length=254, unique=True, verbose_name='Adresse email')),
                ('phone', models.CharField(blank=True, help_text="Numéro de téléphone de l'utilisateur", max_length=20, verbose_name='Téléphone')),
                ('avatar', models.ImageField(blank=True, help_text="Image de profil de l'utilisateur", null=True, upload_to='avatars/', verbose_name='Avatar')),
                ('bio', models.TextField(blank=True, help_text='Texte de présentation ou informations supplémentaires', verbose_name='Biographie')),
                ('role', models.CharField(choices=[('superadmin', 'Super administrateur'), ('admin', 'Administrateur'), ('stagiaire', 'Stagiaire'), ('staff', 'Membre du staff'), ('test', 'Test')], db_index=True, default='stagiaire', help_text="Rôle ou niveau d'accès de l'utilisateur", max_length=20, verbose_name='Rôle')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Utilisateur',
                'verbose_name_plural': 'Utilisateurs',
                'ordering': ['-date_joined'],
                'permissions': [('can_view_all_users', 'Peut voir tous les utilisateurs'), ('can_export_users', 'Peut exporter les données utilisateurs')],
            },
        ),
        migrations.CreateModel(
            name='Centre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('nom', models.CharField(db_index=True, help_text='Nom complet du centre de formation (doit être unique)', max_length=255, unique=True, verbose_name='Nom du centre')),
                ('code_postal', models.CharField(blank=True, help_text='Code postal à 5 chiffres du centre', max_length=5, null=True, validators=[django.core.validators.RegexValidator(message='Le code postal doit contenir exactement 5 chiffres', regex='^\\d{5}$')], verbose_name='Code postal')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Centre',
                'verbose_name_plural': 'Centres',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Formation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('nom', models.CharField(help_text='Intitulé complet de la formation', max_length=255, verbose_name='Nom de la formation')),
                ('start_date', models.DateField(blank=True, help_text='Date de début de la formation', null=True, verbose_name='Date de début')),
                ('end_date', models.DateField(blank=True, help_text='Date de fin de la formation', null=True, verbose_name='Date de fin')),
                ('num_kairos', models.CharField(blank=True, help_text='Identifiant Kairos de la formation', max_length=50, null=True, verbose_name='Numéro Kairos')),
                ('num_offre', models.CharField(blank=True, help_text="Identifiant de l'offre", max_length=50, null=True, verbose_name="Numéro de l'offre")),
                ('num_produit', models.CharField(blank=True, help_text='Identifiant du produit de formation', max_length=50, null=True, verbose_name='Numéro du produit')),
                ('prevus_crif', models.PositiveIntegerField(default=0, help_text='Nombre de places disponibles CRIF', verbose_name='Places prévues CRIF')),
                ('prevus_mp', models.PositiveIntegerField(default=0, help_text='Nombre de places disponibles MP', verbose_name='Places prévues MP')),
                ('inscrits_crif', models.PositiveIntegerField(default=0, help_text="Nombre d'inscrits CRIF", verbose_name='Inscrits CRIF')),
                ('inscrits_mp', models.PositiveIntegerField(default=0, help_text="Nombre d'inscrits MP", verbose_name='Inscrits MP')),
                ('saturation', models.FloatField(blank=True, help_text='Pourcentage moyen de saturation basé sur les commentaires', null=True, verbose_name='Niveau de saturation moyen')),
                ('assistante', models.CharField(blank=True, help_text="Nom de l'assistante responsable", max_length=255, null=True, verbose_name='Assistante')),
                ('cap', models.PositiveIntegerField(blank=True, help_text="Capacité maximale d'accueil", null=True, verbose_name='Capacité maximale')),
                ('convocation_envoie', models.BooleanField(default=False, help_text='Indique si les convocations ont été envoyées', verbose_name='Convocation envoyée')),
                ('entree_formation', models.PositiveIntegerField(default=0, help_text='Nombre de personnes entrées en formation', verbose_name='Entrées en formation')),
                ('nombre_candidats', models.PositiveIntegerField(default=0, help_text='Nombre total de candidats pour cette formation', verbose_name='Nombre de candidats')),
                ('nombre_entretiens', models.PositiveIntegerField(default=0, help_text="Nombre d'entretiens réalisés", verbose_name="Nombre d'entretiens")),
                ('nombre_evenements', models.PositiveIntegerField(default=0, help_text="Nombre d'événements liés à cette formation", verbose_name="Nombre d'événements")),
                ('dernier_commentaire', models.TextField(blank=True, help_text='Contenu du dernier commentaire ajouté', null=True, verbose_name='Dernier commentaire')),
                ('centre', models.ForeignKey(help_text='Centre où se déroule la formation', on_delete=django.db.models.deletion.CASCADE, related_name='formations', to='rap_app.centre', verbose_name='Centre de formation')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
            ],
            options={
                'verbose_name': 'Formation',
                'verbose_name_plural': 'Formations',
                'ordering': ['-start_date', 'nom'],
            },
        ),
        migrations.CreateModel(
            name='Partenaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('type', models.CharField(choices=[('entreprise', 'Entreprise'), ('partenaire', 'Partenaire institutionnel'), ('personne', 'Personne physique')], db_index=True, default='partenaire', help_text="Définit s'il s'agit d'une entreprise, d'un partenaire ou d'une personne physique", max_length=20, verbose_name='Type de partenaire')),
                ('nom', models.CharField(help_text="Nom complet de l'entité", max_length=255, unique=True, verbose_name='Nom')),
                ('secteur_activite', models.CharField(blank=True, help_text="Domaine d'activité principal", max_length=255, null=True, verbose_name="Secteur d'activité")),
                ('street_name', models.CharField(blank=True, help_text='Adresse postale (rue, numéro)', max_length=200, null=True, verbose_name='Adresse')),
                ('zip_code', models.CharField(blank=True, help_text='Code postal à 5 chiffres', max_length=5, null=True, validators=[django.core.validators.RegexValidator(message='Le code postal doit être composé de 5 chiffres.', regex='^[0-9]{5}$')], verbose_name='Code postal')),
                ('city', models.CharField(blank=True, help_text='Ville', max_length=100, null=True, verbose_name='Ville')),
                ('country', models.CharField(blank=True, default='France', help_text='Pays (France par défaut)', max_length=100, null=True, verbose_name='Pays')),
                ('contact_nom', models.CharField(blank=True, help_text='Nom et prénom du contact principal', max_length=255, null=True, verbose_name='Nom du contact')),
                ('contact_poste', models.CharField(blank=True, help_text='Fonction occupée par le contact', max_length=255, null=True, verbose_name='Poste du contact')),
                ('contact_telephone', models.CharField(blank=True, help_text='Numéro de téléphone au format français', max_length=20, null=True, validators=[django.core.validators.RegexValidator(message='Entrez un numéro de téléphone français valide.', regex='^(0[1-9]\\d{8})$|^(?:\\+33|0033)[1-9]\\d{8}$')], verbose_name='Téléphone')),
                ('contact_email', models.EmailField(blank=True, help_text='Adresse email du contact', max_length=254, null=True, verbose_name='Email')),
                ('website', models.URLField(blank=True, help_text='Site web officiel (http:// ou https://)', null=True, validators=[django.core.validators.RegexValidator(message="L'URL doit commencer par http:// ou https://", regex='^(http|https)://')], verbose_name='Site web')),
                ('social_network_url', models.URLField(blank=True, help_text="URL d'un profil LinkedIn, Twitter, etc.", null=True, verbose_name='Réseau social')),
                ('actions', models.CharField(blank=True, choices=[('recrutement_emploi', 'Recrutement - Emploi'), ('recrutement_stage', 'Recrutement - Stage'), ('recrutement_apprentissage', 'Recrutement - Apprentissage'), ('presentation_metier_entreprise', 'Présentation métier/entreprise'), ('visite_entreprise', "Visite d'entreprise"), ('coaching', 'Coaching'), ('partenariat', 'Partenariat'), ('autre', 'Autre'), ('non_definie', 'Non définie')], help_text="Catégorie principale d'interaction avec ce partenaire", max_length=50, null=True, verbose_name="Type d'action")),
                ('action_description', models.TextField(blank=True, help_text='Détails sur les actions menées ou envisagées', null=True, verbose_name="Description de l'action")),
                ('description', models.TextField(blank=True, help_text='Informations générales sur le partenaire', null=True, verbose_name='Description générale')),
                ('slug', models.SlugField(blank=True, help_text='Identifiant URL unique généré automatiquement à partir du nom', max_length=255, null=True, unique=True, verbose_name='Slug')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Partenaire',
                'verbose_name_plural': 'Partenaires',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='VAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('reference', models.CharField(blank=True, help_text='Référence unique de la VAE (générée automatiquement si vide)', max_length=50, verbose_name='Référence')),
                ('statut', models.CharField(choices=[('info', "Demande d'informations"), ('dossier', 'Dossier en cours'), ('attente_financement', 'En attente de financement'), ('accompagnement', 'Accompagnement en cours'), ('jury', 'En attente de jury'), ('terminee', 'VAE terminée'), ('abandonnee', 'VAE abandonnée')], default='info', help_text='Statut actuel de la VAE', max_length=20, verbose_name='Statut')),
                ('commentaire', models.TextField(blank=True, help_text='Notes ou informations supplémentaires sur cette VAE', verbose_name='Commentaire')),
                ('centre', models.ForeignKey(help_text='Centre responsable de cette VAE', on_delete=django.db.models.deletion.CASCADE, related_name='vaes', to='rap_app.centre', verbose_name='Centre')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'VAE',
                'verbose_name_plural': 'VAEs',
                'ordering': ['-created_at', 'centre'],
            },
        ),
        migrations.CreateModel(
            name='TypeOffre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('nom', models.CharField(choices=[('crif', 'CRIF'), ('alternance', 'Alternance'), ('poec', 'POEC'), ('poei', 'POEI'), ('tosa', 'TOSA'), ('autre', 'Autre'), ('non_defini', 'Non défini')], default='non_defini', help_text="Sélectionnez le type d'offre de formation parmi les choix prédéfinis", max_length=100, verbose_name="Type d'offre")),
                ('autre', models.CharField(blank=True, help_text="Si vous avez choisi 'Autre', précisez le type d'offre personnalisé", max_length=255, verbose_name='Autre (personnalisé)')),
                ('couleur', models.CharField(blank=True, help_text="Code couleur hexadécimal (ex: #FF5733) pour l'affichage visuel", max_length=7, null=True, verbose_name='Couleur associée (hexadécimal)')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': "Type d'offre",
                'verbose_name_plural': "Types d'offres",
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='SuiviJury',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('annee', models.PositiveIntegerField(default=2025, help_text='Année au format YYYY (ex: 2024)', validators=[django.core.validators.MinValueValidator(2000)], verbose_name='Année')),
                ('mois', models.PositiveSmallIntegerField(choices=[(1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'), (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')], default=5, help_text="Mois de l'année (1-12)", verbose_name='Mois')),
                ('objectif_jury', models.PositiveIntegerField(default=0, help_text='Nombre de jurys à réaliser pour le mois', verbose_name='Objectif jury')),
                ('jurys_realises', models.PositiveIntegerField(default=0, help_text='Nombre de jurys effectivement réalisés ce mois', verbose_name='Jurys réalisés')),
                ('pourcentage_mensuel', models.DecimalField(decimal_places=2, default=Decimal('0.00'), editable=False, help_text="Pourcentage d'atteinte de l'objectif mensuel (calculé automatiquement)", max_digits=6, verbose_name='Pourcentage mensuel')),
                ('centre', models.ForeignKey(help_text='Centre associé à cet enregistrement', on_delete=django.db.models.deletion.CASCADE, to='rap_app.centre', verbose_name='Centre')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Suivi des jurys',
                'verbose_name_plural': 'Suivis des jurys',
                'ordering': ['annee', 'mois', 'centre'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Statut',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('nom', models.CharField(choices=[('non_defini', 'Non défini'), ('recrutement_en_cours', 'Recrutement en cours'), ('formation_en_cours', 'Formation en cours'), ('formation_a_annuler', 'Formation à annuler'), ('formation_a_repousser', 'Formation à repousser'), ('formation_annulee', 'Formation annulée'), ('pleine', 'Pleine'), ('quasi_pleine', 'Quasi-pleine'), ('autre', 'Autre')], help_text='Identifiant du statut parmi les choix prédéfinis', max_length=100, verbose_name='Nom du statut')),
                ('couleur', models.CharField(blank=True, help_text="Couleur hexadécimale (#RRGGBB) pour l'affichage visuel", max_length=7, verbose_name='Couleur')),
                ('description_autre', models.CharField(blank=True, help_text="Description détaillée requise quand le statut est 'Autre'", max_length=255, null=True, verbose_name='Description personnalisée')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Statut',
                'verbose_name_plural': 'Statuts',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Semaine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('annee', models.PositiveIntegerField(default=0, help_text='Année de la semaine', verbose_name='Année')),
                ('mois', models.PositiveIntegerField(default=1, help_text='Mois de la semaine (1-12)', verbose_name='Mois')),
                ('numero_semaine', models.PositiveIntegerField(default=1, help_text="Numéro de la semaine dans l'année", verbose_name='Numéro de semaine')),
                ('date_debut_semaine', models.DateField(help_text='Premier jour de la semaine', verbose_name='Date de début')),
                ('date_fin_semaine', models.DateField(help_text='Dernier jour de la semaine', verbose_name='Date de fin')),
                ('objectif_annuel_prepa', models.PositiveIntegerField(default=0, help_text='Objectif annuel de préparation', verbose_name='Objectif annuel')),
                ('objectif_mensuel_prepa', models.PositiveIntegerField(default=0, help_text='Objectif mensuel de préparation', verbose_name='Objectif mensuel')),
                ('objectif_hebdo_prepa', models.PositiveIntegerField(default=0, help_text='Objectif hebdomadaire de préparation', verbose_name='Objectif hebdomadaire')),
                ('nombre_places_ouvertes', models.PositiveIntegerField(default=0, help_text='Nombre de places ouvertes pour la semaine', verbose_name='Places ouvertes')),
                ('nombre_prescriptions', models.PositiveIntegerField(default=0, help_text='Nombre de prescriptions reçues', verbose_name='Prescriptions')),
                ('nombre_presents_ic', models.PositiveIntegerField(default=0, help_text='Nombre de personnes présentes en information collective', verbose_name='Présents IC')),
                ('nombre_adhesions', models.PositiveIntegerField(default=0, help_text="Nombre d'adhésions réalisées", verbose_name='Adhésions')),
                ('departements', models.JSONField(blank=True, default=dict, help_text="Nombre d'adhésions par département (format JSON)", null=True, verbose_name='Répartition par département')),
                ('nombre_par_atelier', models.JSONField(blank=True, default=dict, help_text='Nombre de participants par atelier (format JSON)', null=True, verbose_name='Répartition par atelier')),
                ('centre', models.ForeignKey(blank=True, help_text='Centre auquel cette semaine est rattachée', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='semaines', to='rap_app.centre', verbose_name='Centre de formation')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Semaine',
                'verbose_name_plural': 'Semaines',
                'ordering': ['-date_debut_semaine'],
            },
        ),
        migrations.CreateModel(
            name='Rapport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('nom', models.CharField(help_text='Titre descriptif du rapport', max_length=255, verbose_name='Nom du rapport')),
                ('type_rapport', models.CharField(choices=[('occupation', "Rapport d'occupation des formations"), ('centre', 'Rapport de performance par centre'), ('statut', 'Rapport de suivi des statuts'), ('evenement', "Rapport d'efficacité des événements"), ('recrutement', 'Rapport de suivi du recrutement'), ('partenaire', "Rapport d'activité des partenaires"), ('repartition', 'Rapport de répartition des partenaires'), ('periodique', 'Rapport périodique'), ('annuel', 'Rapport annuel consolidé'), ('utilisateur', "Rapport d'activité utilisateurs")], help_text='Catégorie du rapport déterminant son contenu', max_length=50, verbose_name='Type de rapport')),
                ('periode', models.CharField(choices=[('quotidien', 'Quotidien'), ('hebdomadaire', 'Hebdomadaire'), ('mensuel', 'Mensuel'), ('trimestriel', 'Trimestriel'), ('annuel', 'Annuel'), ('personnalise', 'Période personnalisée')], help_text='Fréquence du rapport (pour les rapports récurrents)', max_length=50, verbose_name='Périodicité')),
                ('date_debut', models.DateField(help_text='Date de début de la période couverte par le rapport', verbose_name='Date de début')),
                ('date_fin', models.DateField(help_text='Date de fin de la période couverte par le rapport', verbose_name='Date de fin')),
                ('format', models.CharField(choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV'), ('html', 'HTML')], default='html', help_text='Format de génération du rapport (PDF, Excel, etc.)', max_length=10, verbose_name='Format')),
                ('donnees', models.JSONField(default=dict, help_text='Contenu du rapport au format JSON', verbose_name='Données du rapport')),
                ('temps_generation', models.FloatField(blank=True, help_text='Durée de génération du rapport en secondes', null=True, verbose_name='Temps de génération (s)')),
                ('centre', models.ForeignKey(blank=True, help_text='Centre optionnel pour filtrer les données du rapport', null=True, on_delete=django.db.models.deletion.SET_NULL, to='rap_app.centre', verbose_name='Centre')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('formation', models.ForeignKey(blank=True, help_text='Formation spécifique pour les rapports ciblés', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rapports', to='rap_app.formation', verbose_name='Formation')),
                ('statut', models.ForeignKey(blank=True, help_text='Statut optionnel pour filtrer les données du rapport', null=True, on_delete=django.db.models.deletion.SET_NULL, to='rap_app.statut', verbose_name='Statut')),
                ('type_offre', models.ForeignKey(blank=True, help_text="Type d'offre optionnel pour filtrer les données du rapport", null=True, on_delete=django.db.models.deletion.SET_NULL, to='rap_app.typeoffre', verbose_name="Type d'offre")),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Rapport',
                'verbose_name_plural': 'Rapports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Prospection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('date_prospection', models.DateTimeField(default=django.utils.timezone.now, help_text='Date et heure de la prospection', verbose_name='Date de prospection')),
                ('type_contact', models.CharField(choices=[('premier_contact', 'Premier contact'), ('relance', 'Relance')], default='premier_contact', help_text="Indique s'il s'agit d'un premier contact ou d'une relance", max_length=20, verbose_name='Type de contact')),
                ('motif', models.CharField(choices=[('POEI', 'POEI'), ('apprentissage', 'Apprentissage'), ('VAE', 'VAE'), ('partenariat', 'Établir un partenariat'), ('autre', 'Autre')], help_text='Motif principal de la prospection', max_length=30, verbose_name='Motif')),
                ('statut', models.CharField(choices=[('a_faire', 'À faire'), ('en_cours', 'En cours'), ('a_relancer', 'À relancer'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée'), ('annulee', 'Annulée'), ('non_renseigne', 'Non renseigné')], default='a_faire', help_text='État actuel de la prospection', max_length=20, verbose_name='Statut')),
                ('objectif', models.CharField(choices=[('prise_contact', 'Prise de contact'), ('rendez_vous', 'Obtenir un rendez-vous'), ('presentation_offre', "Présentation d'une offre"), ('contrat', 'Signer un contrat'), ('partenariat', 'Établir un partenariat'), ('autre', 'Autre')], default='prise_contact', help_text='Objectif visé par cette prospection', max_length=30, verbose_name='Objectif')),
                ('commentaire', models.TextField(blank=True, help_text='Notes ou commentaires sur cette prospection', null=True, verbose_name='Commentaire')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('formation', models.ForeignKey(blank=True, help_text='Formation associée à cette prospection (optionnel)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prospections', to='rap_app.formation', verbose_name='Formation')),
                ('partenaire', models.ForeignKey(help_text='Partenaire concerné par cette prospection', on_delete=django.db.models.deletion.CASCADE, related_name='prospections', to='rap_app.partenaire', verbose_name='Partenaire')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Suivi de prospection',
                'verbose_name_plural': 'Suivis de prospections',
                'ordering': ['-date_prospection'],
            },
        ),
        migrations.CreateModel(
            name='PrepaCompGlobal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('annee', models.PositiveIntegerField(default=rap_app.models.prepacomp.PrepaCompGlobal.default_annee, help_text='Année concernée', verbose_name='Année')),
                ('total_candidats', models.PositiveIntegerField(default=0, help_text="Nombre total de candidats pour l'année", verbose_name='Total candidats')),
                ('total_prescriptions', models.PositiveIntegerField(default=0, help_text="Nombre total de prescriptions pour l'année", verbose_name='Total prescriptions')),
                ('adhesions', models.PositiveIntegerField(default=0, help_text="Nombre total d'adhésions pour l'année", verbose_name='Adhésions')),
                ('total_presents', models.PositiveIntegerField(default=0, help_text="Nombre total de personnes présentes en IC pour l'année", verbose_name='Total présents')),
                ('total_places_ouvertes', models.PositiveIntegerField(default=0, help_text="Nombre total de places ouvertes pour l'année", verbose_name='Total places ouvertes')),
                ('objectif_annuel_prepa', models.PositiveIntegerField(default=0, help_text='Objectif annuel de préparation', verbose_name='Objectif annuel prépa')),
                ('objectif_hebdomadaire_prepa', models.PositiveIntegerField(default=0, help_text='Objectif hebdomadaire de préparation', verbose_name='Objectif hebdomadaire prépa')),
                ('objectif_annuel_jury', models.PositiveIntegerField(default=0, help_text='Objectif annuel pour les jurys', verbose_name='Objectif annuel jury')),
                ('objectif_mensuel_jury', models.PositiveIntegerField(default=0, help_text='Objectif mensuel pour les jurys', verbose_name='Objectif mensuel jury')),
                ('centre', models.ForeignKey(blank=True, help_text='Centre auquel ces statistiques sont rattachées', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prepa_globaux', to='rap_app.centre', verbose_name='Centre')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Bilan global PrépaComp',
                'verbose_name_plural': 'Bilans globaux PrépaComp',
                'ordering': ['-annee'],
            },
        ),
        migrations.CreateModel(
            name='LogUtilisateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('object_id', models.PositiveIntegerField()),
                ('action', models.CharField(max_length=255)),
                ('details', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Log utilisateur',
                'verbose_name_plural': 'Logs utilisateur',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HistoriqueStatutVAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('statut', models.CharField(choices=[('info', "Demande d'informations"), ('dossier', 'Dossier en cours'), ('attente_financement', 'En attente de financement'), ('accompagnement', 'Accompagnement en cours'), ('jury', 'En attente de jury'), ('terminee', 'VAE terminée'), ('abandonnee', 'VAE abandonnée')], help_text='Nouveau statut de la VAE', max_length=20, verbose_name='Statut')),
                ('date_changement_effectif', models.DateField(help_text="Date à laquelle le changement de statut a eu lieu (pas nécessairement aujourd'hui)", verbose_name='Date effective du changement')),
                ('commentaire', models.TextField(blank=True, help_text='Notes ou informations supplémentaires sur ce changement de statut', verbose_name='Commentaire')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
                ('vae', models.ForeignKey(help_text='VAE concernée par ce changement de statut', on_delete=django.db.models.deletion.CASCADE, related_name='historique_statuts', to='rap_app.vae', verbose_name='VAE')),
            ],
            options={
                'verbose_name': 'Historique de statut VAE',
                'verbose_name_plural': 'Historiques de statuts VAE',
                'ordering': ['-date_changement_effectif', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='HistoriqueProspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('date_modification', models.DateTimeField(auto_now_add=True, help_text='Date et heure de la modification', verbose_name='Date de modification')),
                ('ancien_statut', models.CharField(choices=[('a_faire', 'À faire'), ('en_cours', 'En cours'), ('a_relancer', 'À relancer'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée'), ('annulee', 'Annulée'), ('non_renseigne', 'Non renseigné')], help_text='Statut avant la modification', max_length=20, verbose_name='Ancien statut')),
                ('nouveau_statut', models.CharField(choices=[('a_faire', 'À faire'), ('en_cours', 'En cours'), ('a_relancer', 'À relancer'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée'), ('annulee', 'Annulée'), ('non_renseigne', 'Non renseigné')], help_text='Statut après la modification', max_length=20, verbose_name='Nouveau statut')),
                ('type_contact', models.CharField(choices=[('premier_contact', 'Premier contact'), ('relance', 'Relance')], default='premier_contact', help_text='Type de contact utilisé', max_length=20, verbose_name='Type de contact')),
                ('commentaire', models.TextField(blank=True, help_text='Commentaire ou note sur la modification', null=True, verbose_name='Commentaire')),
                ('resultat', models.TextField(blank=True, help_text="Résultat ou conséquence de l'action", null=True, verbose_name='Résultat')),
                ('prochain_contact', models.DateField(blank=True, help_text='Date prévue pour le prochain contact', null=True, verbose_name='Prochain contact')),
                ('moyen_contact', models.CharField(blank=True, choices=[('email', 'Email'), ('telephone', 'Téléphone'), ('visite', 'Visite'), ('reseaux', 'Réseaux sociaux')], help_text='Moyen de communication utilisé', max_length=50, null=True, verbose_name='Moyen de contact')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('prospection', models.ForeignKey(help_text='Prospection concernée par cet historique', on_delete=django.db.models.deletion.CASCADE, related_name='historiques', to='rap_app.prospection', verbose_name='Prospection')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Historique de prospection',
                'verbose_name_plural': 'Historiques de prospections',
                'ordering': ['-date_modification'],
            },
        ),
        migrations.CreateModel(
            name='HistoriqueFormation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('action', models.CharField(choices=[('modification', 'Modification'), ('ajout', 'Ajout'), ('suppression', 'Suppression'), ('commentaire', 'Commentaire'), ('document', 'Document'), ('evenement', 'Événement')], default='modification', help_text="Nature de l'action réalisée (ex : modification, ajout)", max_length=100, verbose_name="Type d'action")),
                ('champ_modifie', models.CharField(help_text='Nom du champ ayant été modifié', max_length=100, verbose_name='Champ modifié')),
                ('ancienne_valeur', models.TextField(blank=True, help_text='Valeur avant la modification', null=True, verbose_name='Ancienne valeur')),
                ('nouvelle_valeur', models.TextField(blank=True, help_text='Valeur après la modification', null=True, verbose_name='Nouvelle valeur')),
                ('commentaire', models.TextField(blank=True, help_text='Commentaire explicatif (facultatif)', null=True, verbose_name='Commentaire de modification')),
                ('details', models.JSONField(blank=True, default=dict, help_text='Données contextuelles (ex : ID utilisateur, origine, etc.)', verbose_name='Détails supplémentaires')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('formation', models.ForeignKey(help_text='Formation à laquelle ce changement est associé', on_delete=django.db.models.deletion.CASCADE, related_name='historiques', to='rap_app.formation', verbose_name='Formation concernée')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Historique de modification de formation',
                'verbose_name_plural': 'Historiques de modifications de formations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='formation',
            name='partenaires',
            field=models.ManyToManyField(blank=True, help_text='Partenaires associés à cette formation', related_name='formations', to='rap_app.partenaire', verbose_name='Partenaires'),
        ),
        migrations.AddField(
            model_name='formation',
            name='statut',
            field=models.ForeignKey(help_text='État actuel de la formation', on_delete=django.db.models.deletion.CASCADE, related_name='formations', to='rap_app.statut', verbose_name='Statut de la formation'),
        ),
        migrations.AddField(
            model_name='formation',
            name='type_offre',
            field=models.ForeignKey(help_text="Catégorie d'offre de formation", on_delete=django.db.models.deletion.CASCADE, related_name='formations', to='rap_app.typeoffre', verbose_name="Type d'offre"),
        ),
        migrations.AddField(
            model_name='formation',
            name='updated_by',
            field=models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par'),
        ),
        migrations.CreateModel(
            name='Evenement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('type_evenement', models.CharField(choices=[('info_collective_presentiel', 'Information collective présentiel'), ('info_collective_distanciel', 'Information collective distanciel'), ('job_dating', 'Job dating'), ('evenement_emploi', 'Événement emploi'), ('forum', 'Forum'), ('jpo', 'Journée Portes Ouvertes'), ('autre', 'Autre')], db_index=True, help_text="Catégorie de l'événement (ex : forum, job dating, etc.)", max_length=100, verbose_name="Type d'événement")),
                ('description_autre', models.CharField(blank=True, help_text="Détail du type si 'Autre' est sélectionné", max_length=255, null=True, verbose_name='Description personnalisée')),
                ('details', models.TextField(blank=True, help_text='Détails ou informations supplémentaires', null=True, verbose_name='Détails complémentaires')),
                ('event_date', models.DateField(blank=True, help_text="Date prévue pour l'événement", null=True, verbose_name="Date de l'événement")),
                ('lieu', models.CharField(blank=True, help_text="Lieu où se déroule l'événement", max_length=255, null=True, verbose_name='Lieu')),
                ('participants_prevus', models.PositiveIntegerField(blank=True, help_text='Nombre de personnes attendues', null=True, verbose_name='Participants prévus')),
                ('participants_reels', models.PositiveIntegerField(blank=True, help_text='Nombre de participants présents', null=True, verbose_name='Participants réels')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('formation', models.ForeignKey(blank=True, help_text="Formation associée à l'événement", null=True, on_delete=django.db.models.deletion.CASCADE, related_name='evenements', to='rap_app.formation', verbose_name='Formation')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Événement',
                'verbose_name_plural': 'Événements',
                'ordering': ['-event_date'],
            },
        ),
        migrations.CreateModel(
            name='DummyModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('name', models.CharField(max_length=100)),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Objet de base',
                'verbose_name_plural': 'Objets de base',
                'ordering': ['-created_at'],
                'get_latest_by': 'created_at',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('nom_fichier', models.CharField(db_index=True, help_text='Nom lisible du fichier (sera nettoyé automatiquement)', max_length=255, verbose_name='Nom du fichier')),
                ('fichier', models.FileField(help_text='Fichier à téléverser (PDF, image, etc.). Max : 10 Mo', upload_to=rap_app.models.documents.filepath_for_document, verbose_name='Fichier')),
                ('type_document', models.CharField(choices=[('pdf', 'PDF'), ('image', 'Image'), ('contrat', 'Contrat signé'), ('autre', 'Autre')], db_index=True, default='autre', help_text='Catégorie du document selon son usage ou son format', max_length=20, verbose_name='Type de document')),
                ('source', models.TextField(blank=True, help_text='Texte optionnel indiquant la provenance du document', null=True, verbose_name='Source')),
                ('taille_fichier', models.PositiveIntegerField(blank=True, help_text='Taille du fichier en kilo-octets (calculée automatiquement)', null=True, verbose_name='Taille (Ko)')),
                ('mime_type', models.CharField(blank=True, help_text='Type MIME détecté automatiquement (ex : application/pdf)', max_length=100, null=True, verbose_name='Type MIME')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('formation', models.ForeignKey(help_text='Formation à laquelle ce document est rattaché', on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='rap_app.formation', verbose_name='Formation associée')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Document',
                'verbose_name_plural': 'Documents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Commentaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date et heure de la dernière modification', verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, help_text="Indique si l'objet est actif ou archivé", verbose_name='Actif')),
                ('contenu', models.TextField(help_text='Texte du commentaire (le HTML est automatiquement nettoyé)', verbose_name='Contenu du commentaire')),
                ('saturation', models.PositiveIntegerField(blank=True, help_text='Pourcentage de saturation perçue dans la formation (entre 0 et 100)', null=True, validators=[django.core.validators.MinValueValidator(0, message='La saturation ne peut pas être négative'), django.core.validators.MaxValueValidator(100, message='La saturation ne peut pas dépasser 100%')], verbose_name='Niveau de saturation (%)')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('formation', models.ForeignKey(help_text='Formation à laquelle ce commentaire est associé', on_delete=django.db.models.deletion.CASCADE, related_name='commentaires', to='rap_app.formation', verbose_name='Formation')),
                ('updated_by', models.ForeignKey(blank=True, help_text="Dernier utilisateur ayant modifié l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Commentaire',
                'verbose_name_plural': 'Commentaires',
                'ordering': ['formation', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='vae',
            index=models.Index(fields=['statut'], name='vae_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='vae',
            index=models.Index(fields=['created_at'], name='vae_created_idx'),
        ),
        migrations.AddIndex(
            model_name='vae',
            index=models.Index(fields=['reference'], name='vae_reference_idx'),
        ),
        migrations.AddIndex(
            model_name='vae',
            index=models.Index(fields=['centre', 'statut'], name='vae_centre_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='vae',
            index=models.Index(fields=['centre', 'created_at'], name='vae_centre_created_idx'),
        ),
        migrations.AddIndex(
            model_name='typeoffre',
            index=models.Index(fields=['nom'], name='typeoffre_nom_idx'),
        ),
        migrations.AddIndex(
            model_name='typeoffre',
            index=models.Index(fields=['autre'], name='typeoffre_autre_idx'),
        ),
        migrations.AddConstraint(
            model_name='typeoffre',
            constraint=models.UniqueConstraint(condition=models.Q(('autre__isnull', False), ('nom', 'autre')), fields=('autre',), name='unique_autre_non_null'),
        ),
        migrations.AddIndex(
            model_name='suivijury',
            index=models.Index(fields=['annee', 'mois'], name='periode_idx'),
        ),
        migrations.AddIndex(
            model_name='suivijury',
            index=models.Index(fields=['centre', 'annee', 'mois'], name='cent_periode_idx'),
        ),
        migrations.AddIndex(
            model_name='suivijury',
            index=models.Index(fields=['pourcentage_mensuel'], name='sj_pct_idx'),
        ),
        migrations.AddIndex(
            model_name='suivijury',
            index=models.Index(fields=['objectif_jury', 'jurys_realises'], name='sj_obj_jr_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='suivijury',
            unique_together={('centre', 'annee', 'mois')},
        ),
        migrations.AddIndex(
            model_name='statut',
            index=models.Index(fields=['nom'], name='statut_nom_idx'),
        ),
        migrations.AddIndex(
            model_name='statut',
            index=models.Index(fields=['couleur'], name='statut_couleur_idx'),
        ),
        migrations.AddIndex(
            model_name='semaine',
            index=models.Index(fields=['annee', 'mois'], name='semaine_annee_mois_idx'),
        ),
        migrations.AddIndex(
            model_name='semaine',
            index=models.Index(fields=['centre', 'annee'], name='semaine_centre_annee_idx'),
        ),
        migrations.AddIndex(
            model_name='semaine',
            index=models.Index(fields=['date_debut_semaine'], name='semaine_debut_idx'),
        ),
        migrations.AddIndex(
            model_name='semaine',
            index=models.Index(fields=['date_fin_semaine'], name='semaine_fin_idx'),
        ),
        migrations.AddIndex(
            model_name='semaine',
            index=models.Index(fields=['numero_semaine'], name='semaine_numero_idx'),
        ),
        migrations.AddConstraint(
            model_name='semaine',
            constraint=models.CheckConstraint(check=models.Q(('date_debut_semaine__lte', models.F('date_fin_semaine'))), name='semaine_dates_coherentes'),
        ),
        migrations.AlterUniqueTogether(
            name='semaine',
            unique_together={('numero_semaine', 'annee', 'centre')},
        ),
        migrations.AddIndex(
            model_name='rapport',
            index=models.Index(fields=['created_at'], name='rapport_created_idx'),
        ),
        migrations.AddIndex(
            model_name='rapport',
            index=models.Index(fields=['date_debut', 'date_fin'], name='rapport_periode_idx'),
        ),
        migrations.AddIndex(
            model_name='rapport',
            index=models.Index(fields=['type_rapport'], name='rapport_type_idx'),
        ),
        migrations.AddIndex(
            model_name='rapport',
            index=models.Index(fields=['format'], name='rapport_format_idx'),
        ),
        migrations.AddIndex(
            model_name='rapport',
            index=models.Index(fields=['centre'], name='rapport_centre_idx'),
        ),
        migrations.AddIndex(
            model_name='rapport',
            index=models.Index(fields=['formation'], name='rapport_formation_idx'),
        ),
        migrations.AddIndex(
            model_name='prospection',
            index=models.Index(fields=['statut'], name='prosp_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='prospection',
            index=models.Index(fields=['date_prospection'], name='prosp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='prospection',
            index=models.Index(fields=['partenaire'], name='prosp_partenaire_idx'),
        ),
        migrations.AddIndex(
            model_name='prospection',
            index=models.Index(fields=['formation'], name='prosp_formation_idx'),
        ),
        migrations.AddIndex(
            model_name='prospection',
            index=models.Index(fields=['created_by'], name='prosp_createdby_idx'),
        ),
        migrations.AddIndex(
            model_name='prospection',
            index=models.Index(fields=['motif'], name='prosp_motif_idx'),
        ),
        migrations.AddIndex(
            model_name='prospection',
            index=models.Index(fields=['objectif'], name='prosp_objectif_idx'),
        ),
        migrations.AddConstraint(
            model_name='prospection',
            constraint=models.CheckConstraint(check=models.Q(('date_prospection__lte', django.db.models.functions.datetime.Now())), name='prosp_date_not_future'),
        ),
        migrations.AddConstraint(
            model_name='prospection',
            constraint=models.CheckConstraint(check=models.Q(('statut', 'acceptee'), models.Q(('objectif', 'contrat'), _negated=True), _negated=True), name='prosp_acceptee_contrat'),
        ),
        migrations.AddIndex(
            model_name='prepacompglobal',
            index=models.Index(fields=['centre', 'annee'], name='prepaglobal_centre_annee_idx'),
        ),
        migrations.AddIndex(
            model_name='prepacompglobal',
            index=models.Index(fields=['annee'], name='prepaglobal_annee_idx'),
        ),
        migrations.AddConstraint(
            model_name='prepacompglobal',
            constraint=models.CheckConstraint(check=models.Q(('annee__gte', 2020), ('annee__lte', 2100)), name='prepaglobal_annee_valide'),
        ),
        migrations.AlterUniqueTogether(
            name='prepacompglobal',
            unique_together={('centre', 'annee')},
        ),
        migrations.AddIndex(
            model_name='partenaire',
            index=models.Index(fields=['nom'], name='partenaire_nom_idx'),
        ),
        migrations.AddIndex(
            model_name='partenaire',
            index=models.Index(fields=['secteur_activite'], name='partenaire_secteur_idx'),
        ),
        migrations.AddIndex(
            model_name='partenaire',
            index=models.Index(fields=['slug'], name='partenaire_slug_idx'),
        ),
        migrations.AddIndex(
            model_name='partenaire',
            index=models.Index(fields=['zip_code'], name='partenaire_cp_idx'),
        ),
        migrations.AddIndex(
            model_name='partenaire',
            index=models.Index(fields=['type'], name='partenaire_type_idx'),
        ),
        migrations.AddIndex(
            model_name='partenaire',
            index=models.Index(fields=['actions'], name='partenaire_actions_idx'),
        ),
        migrations.AddConstraint(
            model_name='partenaire',
            constraint=models.CheckConstraint(check=models.Q(('nom', ''), _negated=True), name='partenaire_nom_not_empty'),
        ),
        migrations.AddIndex(
            model_name='historiquestatutvae',
            index=models.Index(fields=['vae', 'statut'], name='hist_vae_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='historiquestatutvae',
            index=models.Index(fields=['date_changement_effectif'], name='hist_vae_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historiquestatutvae',
            index=models.Index(fields=['vae', 'date_changement_effectif'], name='hist_vae_vae_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historiqueprospection',
            index=models.Index(fields=['prospection'], name='histprosp_prosp_idx'),
        ),
        migrations.AddIndex(
            model_name='historiqueprospection',
            index=models.Index(fields=['date_modification'], name='histprosp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historiqueprospection',
            index=models.Index(fields=['prochain_contact'], name='histprosp_next_idx'),
        ),
        migrations.AddIndex(
            model_name='historiqueprospection',
            index=models.Index(fields=['nouveau_statut'], name='histprosp_statut_idx'),
        ),
        migrations.AddConstraint(
            model_name='historiqueprospection',
            constraint=models.CheckConstraint(check=models.Q(('prochain_contact__isnull', True), ('prochain_contact__gte', django.db.models.functions.datetime.Now()), _connector='OR'), name='histprosp_prochain_contact_futur'),
        ),
        migrations.AddIndex(
            model_name='historiqueformation',
            index=models.Index(fields=['-created_at'], name='hist_form_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historiqueformation',
            index=models.Index(fields=['formation'], name='hist_form_formation_idx'),
        ),
        migrations.AddIndex(
            model_name='historiqueformation',
            index=models.Index(fields=['action'], name='hist_form_action_idx'),
        ),
        migrations.AddIndex(
            model_name='historiqueformation',
            index=models.Index(fields=['champ_modifie'], name='hist_form_champ_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['start_date'], name='form_start_date_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['end_date'], name='form_end_date_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['nom'], name='form_nom_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['statut'], name='form_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['type_offre'], name='form_type_offre_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['convocation_envoie'], name='form_convoc_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['centre'], name='form_centre_idx'),
        ),
        migrations.AddIndex(
            model_name='formation',
            index=models.Index(fields=['start_date', 'end_date'], name='form_dates_idx'),
        ),
        migrations.AddConstraint(
            model_name='formation',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('start_date__isnull', True), ('end_date__isnull', True), ('start_date__lte', models.F('end_date')), _connector='OR')), name='formation_dates_coherentes'),
        ),
        migrations.AddIndex(
            model_name='evenement',
            index=models.Index(fields=['event_date'], name='event_date_idx'),
        ),
        migrations.AddIndex(
            model_name='evenement',
            index=models.Index(fields=['type_evenement'], name='event_type_idx'),
        ),
        migrations.AddIndex(
            model_name='evenement',
            index=models.Index(fields=['formation'], name='event_formation_idx'),
        ),
        migrations.AddConstraint(
            model_name='evenement',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('description_autre__isnull', False), ('type_evenement', 'autre')), models.Q(('type_evenement', 'autre'), _negated=True), _connector='OR'), name='autre_needs_description'),
        ),
        migrations.AddIndex(
            model_name='dummymodel',
            index=models.Index(fields=['is_active'], name='rap_app_dummymodel_active_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['nom_fichier'], name='doc_filename_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['formation'], name='doc_formation_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['type_document'], name='doc_type_idx'),
        ),
        migrations.AddIndex(
            model_name='document',
            index=models.Index(fields=['created_at'], name='doc_created_idx'),
        ),
        migrations.AddConstraint(
            model_name='document',
            constraint=models.CheckConstraint(check=models.Q(('nom_fichier__isnull', False), models.Q(('nom_fichier', ''), _negated=True)), name='doc_filename_not_empty'),
        ),
        migrations.AddIndex(
            model_name='commentaire',
            index=models.Index(fields=['created_at'], name='comment_created_idx'),
        ),
        migrations.AddIndex(
            model_name='commentaire',
            index=models.Index(fields=['formation', 'created_at'], name='comment_form_date_idx'),
        ),
        migrations.AddIndex(
            model_name='commentaire',
            index=models.Index(fields=['created_by'], name='comment_author_idx'),
        ),
        migrations.AddIndex(
            model_name='commentaire',
            index=models.Index(fields=['saturation'], name='comment_satur_idx'),
        ),
        migrations.AddConstraint(
            model_name='commentaire',
            constraint=models.CheckConstraint(check=models.Q(('saturation__isnull', True), models.Q(('saturation__gte', 0), ('saturation__lte', 100)), _connector='OR'), name='commentaire_saturation_range'),
        ),
        migrations.AddIndex(
            model_name='centre',
            index=models.Index(fields=['nom'], name='centre_nom_idx'),
        ),
        migrations.AddIndex(
            model_name='centre',
            index=models.Index(fields=['code_postal'], name='centre_cp_idx'),
        ),
        migrations.AddConstraint(
            model_name='centre',
            constraint=models.CheckConstraint(check=models.Q(('nom', ''), _negated=True), name='centre_nom_not_empty'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['role'], name='customuser_role_idx'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['email'], name='customuser_email_idx'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['is_active'], name='customuser_active_idx'),
        ),
    ]



================================================
FILE: rap_app/migrations/0002_alter_logutilisateur_options_and_more.py
================================================
# Generated by Django 4.2.7 on 2025-05-10 11:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('rap_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='logutilisateur',
            options={'ordering': ['-created_at'], 'verbose_name': 'Log utilisateur', 'verbose_name_plural': 'Logs utilisateurs'},
        ),
        migrations.AlterField(
            model_name='logutilisateur',
            name='action',
            field=models.CharField(db_index=True, max_length=255, verbose_name='Action'),
        ),
        migrations.AlterField(
            model_name='logutilisateur',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs_utilisateurs', to='contenttypes.contenttype', verbose_name="Type d'objet"),
        ),
        migrations.AlterField(
            model_name='logutilisateur',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, help_text="Date et heure de création de l'enregistrement", verbose_name='Date de création'),
        ),
        migrations.AlterField(
            model_name='logutilisateur',
            name='created_by',
            field=models.ForeignKey(blank=True, editable=False, help_text="Utilisateur ayant créé l'enregistrement", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)s_set', to=settings.AUTH_USER_MODEL, verbose_name='Créé par'),
        ),
        migrations.AlterField(
            model_name='logutilisateur',
            name='details',
            field=models.TextField(blank=True, null=True, verbose_name='Détails'),
        ),
        migrations.AlterField(
            model_name='logutilisateur',
            name='object_id',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="ID de l'objet"),
        ),
        migrations.AddIndex(
            model_name='logutilisateur',
            index=models.Index(fields=['content_type', 'object_id'], name='log_obj_idx'),
        ),
        migrations.AddIndex(
            model_name='logutilisateur',
            index=models.Index(fields=['created_at'], name='log_date_idx'),
        ),
        migrations.AddIndex(
            model_name='logutilisateur',
            index=models.Index(fields=['action'], name='log_action_idx'),
        ),
    ]



================================================
FILE: rap_app/migrations/__init__.py
================================================




================================================
FILE: rap_app/models/__init__.py
================================================
# models/__init__.py

# Modèles principaux
from .base import BaseModel
from .centres import Centre
from .statut import Statut
from .types_offre import TypeOffre
from .formations import Formation, FormationManager, HistoriqueFormation
from .commentaires import Commentaire
from .evenements import Evenement
from .documents import Document
from .partenaires import Partenaire
from .rapports import Rapport
from .prospection import Prospection, HistoriqueProspection
from .prepacomp import Semaine, PrepaCompGlobal
from .vae_jury import VAE, SuiviJury, HistoriqueStatutVAE
from .logs import LogUtilisateur
from .custom_user import CustomUser
from .models_test import DummyModel


__all__ = ['CustomUser']  # Important pour l'importation

default_app_config = "rap_app.apps.RapAppConfig"


# ✅ Import des fichiers contenant des signaux (obligatoire pour qu'ils soient déclenchés)
from . import (
    centres,
    commentaires,
    documents,
    evenements,
    formations,
    logs,
    partenaires,
    prepacomp,
    prospection,
    rapports,
    statut,
    types_offre,
    custom_user,
    vae_jury,
)



================================================
FILE: rap_app/models/base.py
================================================
import logging
from django.db import models
from django.utils.timezone import now
from django.conf import settings
from django.forms.models import model_to_dict
from django.core.cache import cache
from django.core.exceptions import FieldError, ValidationError

from ..middleware import get_current_user

logger = logging.getLogger(__name__)


class BaseModel(models.Model):
    """
    🔧 Modèle de base abstrait pour tous les modèles métiers de l'application.

    Fournit automatiquement :
    - ⏱️ Suivi des dates de création/modification (`created_at`, `updated_at`)
    - 👤 Suivi des utilisateurs (`created_by`, `updated_by`)
    - 🔄 Mise à jour intelligente de `updated_at` uniquement en cas de changement réel
    - 📓 Logging détaillé (conditionnel via `settings.ENABLE_MODEL_LOGGING`)
    - 🔄 Méthodes utilitaires pour la sérialisation et le suivi des modifications
    - 🔒 Validations et gestion des erreurs robustes
    - 📊 Optimisations de performance (cache, détection des changements)
    - 🗑️ Champ `is_active` pour la suppression logique

    👉 À hériter dans tous les modèles personnalisés de l'application.
    """

    created_at = models.DateTimeField(
        auto_now_add=True, 
        editable=False, 
        verbose_name="Date de création",
        help_text="Date et heure de création de l'enregistrement"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Date de mise à jour",
        help_text="Date et heure de la dernière modification"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, 
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="created_%(class)s_set",
        verbose_name="Créé par",
        help_text="Utilisateur ayant créé l'enregistrement"
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_%(class)s_set",
        verbose_name="Modifié par",
        help_text="Dernier utilisateur ayant modifié l'enregistrement"
    )

    is_active = models.BooleanField(
        default=True, 
        verbose_name="Actif",
        help_text="Indique si l'objet est actif ou archivé"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        get_latest_by = 'created_at'
        verbose_name = "Objet de base"
        verbose_name_plural = "Objets de base"
        indexes = [
            models.Index(fields=['is_active'], name='%(app_label)s_%(class)s_active_idx'),
        ]

    def __str__(self):
        """
        🔁 Représentation textuelle par défaut de l'objet.

        Returns:
            str: Format générique du type `NomClasse #id`
        """
        return f"{self.__class__.__name__} #{self.pk}"

    def __repr__(self):
        """
        📝 Représentation technique pour le débogage.
        
        Returns:
            str: Format technique détaillé
        """
        return f"<{self.__class__.__name__}(id={self.pk})>"

    def clean(self):
        """
        🔍 Validation personnalisée à surcharger dans les sous-classes.
        
        Cette méthode est appelée avant la sauvegarde de l'objet pour
        effectuer des validations qui ne peuvent pas être exprimées par
        des contraintes sur les champs individuels.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        pass

    def validate_unique(self, exclude=None):
        """
        🔍 Surcharge de la validation d'unicité avec des messages d'erreur plus clairs.
        
        Améliore les messages d'erreur en ajoutant le nom verbeux des champs.
        
        Args:
            exclude (list): Champs à exclure de la validation
            
        Raises:
            ValidationError: Si les contraintes d'unicité ne sont pas respectées
        """
        try:
            super().validate_unique(exclude=exclude)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                for field, msgs in e.message_dict.items():
                    try:
                        field_verbose = self._meta.get_field(field).verbose_name
                        e.message_dict[field] = [f"{field_verbose}: {msg}" for msg in msgs]
                    except Exception:
                        continue
            raise e


    @classmethod
    def get_current_user(cls):
        """
        👤 Récupère l'utilisateur actuel à partir du contexte.
        
        Utilise le middleware ThreadLocal pour récupérer l'utilisateur actuel.
        
        Returns:
            User: L'utilisateur actuellement connecté ou None si non disponible
        """
        try:
            return get_current_user()
        except ImportError:
            logger.debug("Middleware get_current_user() non disponible.")
            return None
        except AttributeError:
            logger.debug("Aucun utilisateur trouvé dans le contexte.")
            return None
        except Exception as e:
            logger.debug(f"Erreur lors de la récupération de l'utilisateur: {str(e)}")
            return None

    def get_changed_fields(self):
        """
        🔍 Retourne les champs modifiés par rapport à la version enregistrée en base.
        
        Compare les valeurs actuelles avec celles en base de données pour
        détecter les modifications sur tous les champs (sauf les champs d'audit).
        
        Returns:
            dict: Dictionnaire au format {champ: (ancienne_valeur, nouvelle_valeur)}
        """
        if not self.pk:
            return {}
        try:
            old = type(self).objects.get(pk=self.pk)
            changes = {}
            for field in self._meta.fields:
                name = field.name
                if name in ('created_at', 'updated_at', 'created_by', 'updated_by'):
                    continue
                old_val = getattr(old, name, None)
                new_val = getattr(self, name, None)
                if old_val != new_val:
                    changes[name] = (old_val, new_val)
            return changes
        except type(self).DoesNotExist:
            return {}

    def log_debug(self, message):
        """
        📓 Journalise un message de débogage si le paramètre `ENABLE_MODEL_LOGGING` est activé.
        
        Args:
            message (str): Message à journaliser
        """
        if getattr(settings, 'ENABLE_MODEL_LOGGING', settings.DEBUG):
            logger.debug(f"[{self.__class__.__name__}] {message}")

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde l'objet avec gestion automatique des utilisateurs et journalisation.
        
        - Affecte `created_by` et `updated_by` si l'utilisateur est fourni
        - Valide les données avec `clean()` sauf si `skip_validation=True`
        - Journalise les actions si `settings.ENABLE_MODEL_LOGGING` est activé
        - Invalide le cache après la sauvegarde
        """
        user = kwargs.pop('user', None) or self.get_current_user()
        skip_validation = kwargs.pop('skip_validation', False)
        is_new = self.pk is None
        changed_fields = {} if is_new else self.get_changed_fields()

        if is_new and user and not self.created_by:
            self.created_by = user
        if user:
            self.updated_by = user

        try:
            if not skip_validation:
                self.clean()
        except Exception as e:
            model_name = self.__class__.__name__
            logger.error(f"Erreur de validation pour {model_name} (ID: {self.pk or 'nouveau'}): {e}")
            raise

        self.log_debug(f"{'Création' if is_new else 'Mise à jour'} par {user}")
        if changed_fields:
            self.log_debug(f"Changements détectés : {changed_fields}")

        super().save(*args, **kwargs)
        self.invalidate_caches()
        self.log_debug(f"#{self.pk} sauvegardé.")

    def delete(self, *args, **kwargs):
        """
        🗑️ Supprime l'objet avec journalisation et invalidation du cache.
        
        Args:
            *args: Arguments positionnels à transmettre à `models.Model.delete()`
            **kwargs: Arguments nommés pouvant inclure `user` pour l'utilisateur effectuant l'action
            
        Returns:
            tuple: Résultat de la suppression (nombre d'objets supprimés, dict avec détail par type)
        """
        user = kwargs.pop('user', None) or self.get_current_user()
        self.log_debug(f"Suppression de #{self.pk} par {user}")
        self.invalidate_caches()
        result = super().delete(*args, **kwargs)
        self.log_debug(f"#{self.pk} supprimé.")
        return result

    def to_serializable_dict(self, exclude=None):
        """
        📦 Retourne un dictionnaire sérialisable de l'objet.
        
        Convertit toutes les valeurs de l'objet (y compris les relations) 
        en types sérialisables pour JSON ou autre format d'échange.
        
        Args:
            exclude (list): Liste de champs à exclure
            
        Returns:
            dict: Dictionnaire des données sérialisables
        """
        exclude = exclude or []
        data = {}
        
        # Champs simples
        for field in self._meta.fields:
            name = field.name
            if name in exclude:
                continue
            value = getattr(self, name)
            
            # Conversion spécifique selon le type
            if hasattr(value, 'isoformat'):  # Date/datetime
                data[name] = value.isoformat()
            elif hasattr(value, 'url'):  # FileField/ImageField
                data[name] = value.url
            elif isinstance(value, models.Model):  # ForeignKey
                data[name] = {'id': value.pk, 'str': str(value)}
            else:  # Types simples
                data[name] = value

        # Relations many-to-many
        for field in self._meta.many_to_many:
            if field.name in exclude:
                continue
            related_objects = getattr(self, field.name).all()
            data[field.name] = [{'id': obj.pk, 'str': str(obj)} for obj in related_objects]

        return data

    @classmethod
    def get_verbose_name(cls):
        """
        🔠 Retourne le nom verbeux du modèle.
        
        Returns:
            str: Nom verbeux défini dans les métadonnées
        """
        return cls._meta.verbose_name

    @classmethod
    def get_by_id(cls, id, active_only=True):
        """
        🔍 Récupère un objet par son ID avec gestion des erreurs.
        
        Args:
            id: Identifiant de l'objet
            active_only (bool): Si True, ne récupère que les objets actifs
            
        Returns:
            Object: L'instance correspondant à l'ID
            
        Raises:
            ValueError: Si l'ID est vide ou invalide
            DoesNotExist: Si aucun objet ne correspond
        """
        if not id:
            raise ValueError("L'identifiant ne peut pas être vide.")
        try:
            id = int(id)
            qs = cls.objects
            if active_only:
                qs = qs.filter(is_active=True)
            return qs.get(pk=id)
        except (ValueError, TypeError):
            raise ValueError(f"Identifiant invalide : {id}")
        except cls.DoesNotExist:
            logger.warning(f"{cls.__name__} avec ID={id} non trouvé")
            raise

    def invalidate_caches(self):
        """
        🔄 Invalide les caches associés à cet objet.
        
        Cette méthode peut être étendue dans les sous-classes pour
        invalider des caches supplémentaires spécifiques.
        """
        cache.delete(f"{self.__class__.__name__}_{self.pk}")
        cache.delete(f"{self.__class__.__name__}_list")

    @classmethod
    def get_filtered_queryset(cls, **filters):
        """
        🔍 Retourne un queryset filtré avec gestion des erreurs.
        
        Args:
            **filters: Filtres à appliquer au queryset
            
        Returns:
            QuerySet: QuerySet filtré ou vide en cas d'erreur
        """
        try:
            return cls.objects.filter(**filters)
        except (FieldError, ValueError) as e:
            logger.error(f"Erreur de filtrage sur {cls.__name__}: {e}")
            return cls.objects.none()


================================================
FILE: rap_app/models/centres.py
================================================
from django.utils.timezone import now 
import logging
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.functional import cached_property
from django.db.models import Count, F, Q

from .base import BaseModel

logger = logging.getLogger(__name__)

class CentreManager(models.Manager):
    """
    Manager personnalisé pour le modèle Centre.
    Fournit des méthodes utilitaires pour les requêtes fréquentes.
    """
    
    def actifs(self):
        """
        Retourne uniquement les centres actifs.
        
        Returns:
            QuerySet: Les centres actifs uniquement
        """
        # Si vous ajoutez un champ statut:
        # return self.filter(statut='actif')
        return self.all()
    
    def with_prepa_counts(self):
        """
        Retourne les centres avec le nombre d'objectifs annuels.
        
        Returns:
            QuerySet: Centres annotés avec le nombre de PrepaCompGlobal
        """
        return self.annotate(prepa_count=Count('prepa_globaux'))
    
    def by_code_postal(self, code_postal):
        """
        Filtre les centres par code postal.
        
        Args:
            code_postal (str): Code postal à rechercher
            
        Returns:
            QuerySet: Centres filtrés par code postal
        """
        return self.filter(code_postal=code_postal)
    
    def with_prepa_for_year(self, year=None):
        """
        Récupère les centres avec leur PrepaCompGlobal pour une année donnée.
        
        Args:
            year (int, optional): Année cible, par défaut l'année courante
            
        Returns:
            QuerySet: Centres avec PrepaCompGlobal préchargés
        """
        from .prepacomp import PrepaCompGlobal
        
        annee = annee or now().year
        
        return self.prefetch_related(
            models.Prefetch(
                'prepacompglobal_set',
                queryset=PrepaCompGlobal.objects.filter(annee=year),
                to_attr='prepa_for_year'
            )
        )
    
    def search(self, query):
        """
        Recherche textuelle dans les centres.
        
        Args:
            query (str): Texte à rechercher
            
        Returns:
            QuerySet: Centres correspondant à la recherche
        """
        if not query:
            return self.all()
            
        return self.filter(
            Q(nom__icontains=query) | 
            Q(code_postal__startswith=query)
        )


class Centre(BaseModel):
    """
    Modèle représentant un centre de formation.
    
    Ce modèle stocke les informations de base d'un centre de formation,
    notamment son nom unique et sa localisation (code postal).
    
    Attributs:
        nom (str): Nom unique du centre (max 255 caractères)
        code_postal (str, optional): Code postal à 5 chiffres du centre
        
    Propriétés:
        full_address: Adresse formatée sous forme de texte
        nb_prepa_comp_global: Nombre d'objectifs annuels associés (mise en cache)
        
    Relations:
        prepa_global: Relations OneToMany avec PrepaCompGlobal
        
    Méthodes:
        clean: Validation spécifique pour le code postal
        to_serializable_dict: Représentation JSON du centre
        invalidate_caches: Invalide les caches de propriétés
        to_csv_row: Convertit l'instance en ligne CSV
    """
    # Constantes pour éviter les valeurs magiques
    NOM_MAX_LENGTH = 255
    CODE_POSTAL_LENGTH = 5
    
    # Choix pour un éventuel statut (à ajouter si pertinent)
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('temporaire', 'Temporaire'),
    ]

    nom = models.CharField(
        max_length=NOM_MAX_LENGTH,
        unique=True,
        verbose_name="Nom du centre",
        help_text="Nom complet du centre de formation (doit être unique)",
        db_index=True,  # Optimisation: ajout explicite d'index pour le nom
    )

    code_postal = models.CharField(
        max_length=CODE_POSTAL_LENGTH,
        null=True,
        blank=True,
        verbose_name="Code postal",
        help_text="Code postal à 5 chiffres du centre",
        validators=[
            RegexValidator(
                regex=r'^\d{5}$',
                message="Le code postal doit contenir exactement 5 chiffres"
            )
        ]
    )
    
    # Optionnel: statut du centre (selon vos besoins)
    # statut = models.CharField(
    #     max_length=20,
    #     choices=STATUS_CHOICES,
    #     default='actif',
    #     verbose_name="Statut du centre",
    #     help_text="État actuel du centre"
    # )

    # Champs optionnels à ajouter selon vos besoins métier
    # region = models.CharField(max_length=100, blank=True, verbose_name="Région")
    # ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    # adresse = models.CharField(max_length=255, blank=True, verbose_name="Adresse")
    
    # Managers
    objects = models.Manager()  # Manager par défaut
    custom = CentreManager()    # Manager personnalisé
    
    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['nom']
        indexes = [
            models.Index(fields=['nom'], name='centre_nom_idx'),
            models.Index(fields=['code_postal'], name='centre_cp_idx'),
            # Ajouter d'autres index composites si nécessaire:
            # models.Index(fields=['region', 'ville'], name='centre_region_ville_idx'),
        ]
        # Contraintes optionnelles
        constraints = [
            # Exemple de contrainte check
            models.CheckConstraint(
                check=~Q(nom=''), 
                name='centre_nom_not_empty'
            ),
        ]
    
    class APIInfo:
        """Informations pour la documentation API."""
        description = "Centres de formation"
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
        filterable_fields = ['nom', 'code_postal']
        searchable_fields = ['nom']
        ordering_fields = ['nom', 'created_at']

    def __str__(self):
        """Représentation textuelle du centre."""
        return self.nom

    def __repr__(self):
        """Représentation pour le débogage."""
        return f"<Centre {self.pk}: {self.nom}>"

    def full_address(self) -> str:
        """Retourne l'adresse complète sous forme textuelle."""
        address = self.nom
        if self.code_postal:
            address += f" ({self.code_postal})"
        return address
    from django.utils.functional import cached_property

    @cached_property
    def nb_prepa_comp_global(self):
        """
        Nombre d'objectifs annuels associés à ce centre.
        Utilisation de cached_property pour optimiser les performances.
        
        Returns:
            int: Nombre d'objectifs PrepaCompGlobal associés
        """
        from .prepacomp import PrepaCompGlobal
        return PrepaCompGlobal.objects.filter(centre=self).count()

    
    # Suppression de la propriété is_active qui masquait potentiellement
    # un champ is_active hérité de BaseModel
    
    # Si nécessaire, ajouter une propriété avec un nom différent:
    # @property
    # def is_actif_par_statut(self):
    #     """
    #     Détermine si le centre est actif selon son statut.
    #     Returns:
    #         bool: True si le centre a un statut actif, False sinon
    #     """
    #     return self.statut == 'actif' if hasattr(self, 'statut') else True

    def invalidate_caches(self):
        """
        Invalide toutes les propriétés mises en cache avec @cached_property.
        """
        for prop in ['nb_prepa_comp_global']:
            self.__dict__.pop(prop, None)


    def to_serializable_dict(self, include_related=False) -> dict:
        """
        Renvoie un dictionnaire JSON-serializable de l'objet.
        
        Args:
            include_related (bool): Si True, inclut les objets liés
            
        Returns:
            dict: Représentation sérialisable du centre
        """
        base_dict = super().to_serializable_dict(exclude=['created_by', 'updated_by'])
        
        centre_dict = {
            "id": self.pk,
            "nom": self.nom,
            "code_postal": self.code_postal,
            "full_address": self.full_address(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Fusionner avec le dictionnaire de base
        result = {**base_dict, **centre_dict}
        
        # Ajouter les objets liés si demandé
        if include_related:
            from .prepacomp import PrepaCompGlobal
            current_year = now().year  
            prepa_global = PrepaCompGlobal.objects.filter(
                centre=self, 
                annee=current_year
            ).first()
            
            if prepa_global:
                result["prepa_global"] = {
                    "id": prepa_global.pk,
                    "annee": prepa_global.annee,
                    # Ajouter d'autres champs pertinents
                }
        
        return result

    def save(self, *args, **kwargs):
        """
        Sauvegarde le centre avec journalisation améliorée.
        Préserve la compatibilité avec le code existant.
        
        Args:
            *args: Arguments positionnels pour save()
            **kwargs: Arguments nommés pour save(), y compris user
        """
        user = kwargs.pop("user", None)
        is_new = self.pk is None

        if is_new:
            logger.info(f"[Centre] Création: {self.nom}")
        else:
            try:
                old = Centre.objects.get(pk=self.pk)
                changes = []
                if old.nom != self.nom:
                    changes.append(f"nom: '{old.nom}' → '{self.nom}'")
                if old.code_postal != self.code_postal:
                    changes.append(f"code_postal: '{old.code_postal}' → '{self.code_postal}'")
                if changes:
                    logger.info(f"[Centre] Modif #{self.pk}: {', '.join(changes)}")
            except Centre.DoesNotExist:
                logger.warning(f"[Centre] Ancienne instance introuvable pour {self.pk}")

        # Validation métier avant sauvegarde
        self.clean()
        
        # Appel de la méthode save du BaseModel avec l'utilisateur directement
        super().save(*args, user=user, **kwargs)

        logger.debug(f"[Centre] Sauvegarde complète de #{self.pk} (user={user})")
        
        # Invalidation du cache
        self.invalidate_caches()

    def delete(self, *args, **kwargs):
        """
        Supprime le centre avec journalisation.
        
        Args:
            *args: Arguments positionnels pour delete()
            **kwargs: Arguments nommés pour delete()
            
        Returns:
            tuple: Résultat de la suppression (nombre d'objets, dict par type)
        """
        logger.warning(f"[Centre] Suppression du centre #{self.pk}: {self.nom}")
        
        # Invalidation du cache avant suppression
        self.invalidate_caches()
        
        # Suppression effective
        return super().delete(*args, **kwargs)

    def clean(self):
        """
        Validation métier spécifique pour le centre.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation du code postal
        if self.code_postal:
            if not self.code_postal.isdigit():
                raise ValidationError({"code_postal": "Le code postal doit être numérique."})
            if len(self.code_postal) != self.CODE_POSTAL_LENGTH:
                raise ValidationError({"code_postal": f"Le code postal doit contenir exactement {self.CODE_POSTAL_LENGTH} chiffres."})

    def prepa_global(self, annee=None):
        """
        Raccourci pour accéder à l'objectif annuel via PrepaCompGlobal.
        
        Args:
            annee (int, optional): Année de référence, par défaut l'année en cours
            
        Returns:
            PrepaCompGlobal: L'instance pour ce centre et cette année, ou None
        """
        from .prepacomp import PrepaCompGlobal
        annee = annee or now().year
        return PrepaCompGlobal.objects.filter(centre=self, annee=annee).first()
    
    def mark_as_inactive(self):
        """
        Marque le centre comme inactif (si un champ statut existe).
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        # Si vous ajoutez un champ statut:
        # self.statut = 'inactif'
        # self.save()
        # return True
        logger.warning(f"[Centre] Tentative de désactivation du centre #{self.pk}, mais pas de champ statut")
        return False
    
    def handle_related_update(self, related_object):
        """
        Gère la mise à jour des objets liés.
        À appeler lorsqu'un objet lié est modifié.
        
        Args:
            related_object: L'objet lié qui a été modifié
        """
        logger.info(f"[Centre] Objet lié mis à jour pour le centre {self.nom}: {related_object}")
        
        # Invalidation du cache
        self.invalidate_caches()
    
    @classmethod
    def get_centres_by_region(cls, region=None):
        """
        Méthode de classe pour récupérer les centres par région.
        Exemple de méthode utilitaire à implémenter si vous ajoutez un champ region.
        
        Args:
            region (str, optional): Région à filtrer, tous si None
            
        Returns:
            QuerySet: Les centres de la région spécifiée ou tous
        """
        queryset = cls.objects.all()
        
        # Si vous ajoutez un champ region:
        # if region:
        #     queryset = queryset.filter(region=region)
        
        return queryset.order_by('nom')
    
    @classmethod
    def get_centres_with_stats(cls):
        """
        Récupère tous les centres avec des statistiques calculées.
        Utilise des annotations pour optimiser les performances.
        
        Returns:
            QuerySet: Centres avec statistiques annotées
        """
        # Utilisation du manager personnalisé
        return cls.custom.with_prepa_counts().order_by('nom')
    
    @classmethod
    def get_csv_fields(cls):
        """
        Définit les champs à inclure dans un export CSV.
        
        Returns:
            list: Liste des noms de champs
        """
        return ['id', 'nom', 'code_postal', 'created_at', 'updated_at']
    
    @classmethod
    def get_csv_headers(cls):
        """
        Définit les en-têtes pour un export CSV.
        
        Returns:
            list: Liste des en-têtes de colonnes
        """
        return [
            'ID', 
            'Nom du centre', 
            'Code postal', 
            'Date de création', 
            'Date de mise à jour'
        ]
    
    def to_csv_row(self):
        """
        Convertit l'instance en ligne CSV.
        
        Returns:
            list: Valeurs pour une ligne CSV
        """
        return [
            self.pk,
            self.nom,
            self.code_postal or '',
            self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        ]


================================================
FILE: rap_app/models/commentaires.py
================================================
import logging
from datetime import timedelta
from django.db import models
from django.db.models import Q, F, Avg, Count
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from .base import BaseModel
from .formations import Formation

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# Signaux déplacés dans signals/commentaires.py
# ----------------------------------------------------


class CommentaireManager(models.Manager):
    """
    Manager personnalisé pour le modèle Commentaire.
    Fournit des méthodes optimisées pour les requêtes courantes.
    """
    
    def recents(self, days=7):
        """
        Retourne les commentaires postés dans les derniers jours.
        
        Args:
            days (int): Nombre de jours à considérer comme récents
            
        Returns:
            QuerySet: Commentaires récents
        """
        date_limite = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=date_limite)
    
    def for_formation(self, formation_id):
        """
        Retourne tous les commentaires pour une formation donnée.
        
        Args:
            formation_id (int): ID de la formation
            
        Returns:
            QuerySet: Commentaires liés à la formation spécifiée
        """
        return self.filter(formation_id=formation_id).select_related('created_by')
    
    def with_saturation(self):
        """
        Retourne uniquement les commentaires avec une valeur de saturation.
        
        Returns:
            QuerySet: Commentaires avec saturation renseignée
        """
        return self.exclude(saturation__isnull=True)
    
    def search(self, query):
        """
        Recherche dans les commentaires.
        
        Args:
            query (str): Terme de recherche
            
        Returns:
            QuerySet: Commentaires correspondants
        """
        if not query:
            return self.all()
        
        return self.filter(Q(contenu__icontains=query) | 
                          Q(created_by__username__icontains=query) |
                          Q(formation__nom__icontains=query))


class Commentaire(BaseModel):
    """
    💬 Modèle représentant un commentaire associé à une formation.

    Un commentaire est rédigé par un utilisateur (ou anonyme) et lié à une formation.
    Il peut contenir un contenu libre, une saturation exprimée en %, et des métadonnées utiles.
    
    Attributs:
        formation (Formation): Formation commentée (relation ForeignKey)
        contenu (str): Texte du commentaire
        saturation (int, optional): Niveau de saturation perçue (0-100%)
        
    Propriétés:
        auteur_nom (str): Nom de l'auteur ou "Anonyme"
        date_formatee (str): Date formatée (JJ/MM/AAAA)
        heure_formatee (str): Heure formatée (HH:MM)
        is_recent (bool): Indique si le commentaire est récent
        
    Méthodes:
        get_content_preview: Aperçu tronqué du contenu
        is_recent: Vérifie si le commentaire est récent
        to_serializable_dict: Dict sérialisable du commentaire
    """
    
    # Constantes pour éviter les valeurs magiques
    SATURATION_MIN = 0
    SATURATION_MAX = 100
    PREVIEW_DEFAULT_LENGTH = 50
    RECENT_DEFAULT_DAYS = 7

    # === Champs relationnels ===
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name="commentaires",
        verbose_name="Formation",
        help_text="Formation à laquelle ce commentaire est associé"
    )

    # === Champs principaux ===
    contenu = models.TextField(
        verbose_name="Contenu du commentaire",
        help_text="Texte du commentaire (le HTML est automatiquement nettoyé)"
    )

    saturation = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Niveau de saturation (%)",
        help_text="Pourcentage de saturation perçue dans la formation (entre 0 et 100)",
        validators=[
            MinValueValidator(SATURATION_MIN, message="La saturation ne peut pas être négative"),
            MaxValueValidator(SATURATION_MAX, message="La saturation ne peut pas dépasser 100%")
        ]
    )
    
    # === Managers === 
    objects = models.Manager()  # Manager par défaut
    custom = CommentaireManager()  # Manager personnalisé

    # === Méta options ===
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['formation', '-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='comment_created_idx'),
            models.Index(fields=['formation', 'created_at'], name='comment_form_date_idx'),
            models.Index(fields=['created_by'], name='comment_author_idx'),
            models.Index(fields=['saturation'], name='comment_satur_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(saturation__isnull=True) | Q(saturation__gte=0) & Q(saturation__lte=100),
                name='commentaire_saturation_range'
            )
        ]

    def __str__(self):
        """
        🔁 Représentation textuelle du commentaire.
        """
        auteur = self.created_by.username if self.created_by else "Anonyme"
        return f"Commentaire de {auteur} sur {self.formation.nom} ({self.created_at.strftime('%d/%m/%Y')})"
        
    def __repr__(self):
        """
        Représentation technique pour le débogage.
        """
        return f"<Commentaire(id={self.pk}, formation={self.formation_id}, auteur={self.created_by_id})>"

    def clean(self):
        """
        Validation métier spécifique pour le commentaire.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        # Validation de la saturation
        if self.saturation is not None:
            if self.saturation < self.SATURATION_MIN or self.saturation > self.SATURATION_MAX:
                raise ValidationError({
                    'saturation': f"La saturation doit être comprise entre {self.SATURATION_MIN} et {self.SATURATION_MAX}%"
                })
        
        # Validation du contenu (non vide)
        if not self.contenu.strip():
            raise ValidationError({
                'contenu': "Le contenu ne peut pas être vide"
            })

    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde le commentaire après nettoyage et validation.

        - Supprime tout HTML du contenu via `strip_tags`.
        - Vérifie et contraint la valeur de `saturation` entre 0 et 100.
        - Validation des données métier via `clean()`.

        Args:
            *args: Arguments positionnels pour `super().save()`.
            **kwargs: Arguments nommés pour `super().save()`.

        Returns:
            None
        """
        # Nettoyer et valider les données
        self.contenu = strip_tags(self.contenu)
        
        if self.saturation is not None:
            self.saturation = max(self.SATURATION_MIN, min(self.SATURATION_MAX, self.saturation))
            
        # Validation métier
        self.clean()
        
        # Conserver l'état "is_new" pour le logging
        is_new = self.pk is None
        
        # Enregistrer l'objet
        super().save(*args, **kwargs)
        
        logger.debug(f"Commentaire #{self.pk} {'créé' if is_new else 'mis à jour'} pour la formation #{self.formation_id}")
        
    def delete(self, *args, **kwargs):
        """
        🗑️ Supprime le commentaire et met à jour la formation associée.
        
        Args:
            *args: Arguments positionnels pour `super().delete()`.
            **kwargs: Arguments nommés pour `super().delete()`.
            update_formation (bool, optional): Mettre à jour les infos de la formation
            
        Returns:
            tuple: Résultat de la suppression
        """
        # Récupérer et supprimer le paramètre update_formation
        update_formation = kwargs.pop('update_formation', True)
        
        # Conserver une référence à la formation
        formation = self.formation if update_formation else None
        
        # Supprimer l'objet
        result = super().delete(*args, **kwargs)
        
        # Mettre à jour la formation si demandé
        if update_formation and formation:
            self.update_formation_static(formation)
            
        logger.debug(f"Commentaire #{self.pk} supprimé pour la formation #{self.formation_id}")
        
        return result

    def update_formation(self):
        """
        🔄 Met à jour les informations de la formation liée à ce commentaire.
        
        Met à jour:
        - Le champ dernier_commentaire de la formation
        - La saturation moyenne si applicable
        - Le compteur de commentaires
        
        Notes:
            Cette méthode ne devrait généralement pas être appelée directement.
        """
        # Assurez-vous que cette méthode existe dans votre modèle Formation
        if hasattr(self.formation, 'update_from_commentaires'):
            self.formation.update_from_commentaires()
        else:
            # Implémentation de secours si la méthode n'existe pas
            from django.db.models import Avg
            
            # Mise à jour du dernier commentaire
            self.formation.dernier_commentaire = (
                Commentaire.objects.filter(formation=self.formation)
                .order_by('-created_at')
                .first()
            )
            
            # Calcul de la saturation moyenne
            saturation_avg = (
                Commentaire.objects.filter(formation=self.formation, saturation__isnull=False)
                .aggregate(Avg('saturation'))
                .get('saturation__avg')
            )
            
            # Mise à jour de la formation
            if hasattr(self.formation, 'saturation_moyenne'):
                self.formation.saturation_moyenne = saturation_avg
                
            # Compter les commentaires
            if hasattr(self.formation, 'nb_commentaires'):
                self.formation.nb_commentaires = (
                    Commentaire.objects.filter(formation=self.formation).count()
                )
                
            # Sauvegarder la formation (avec update_fields si possible)
            update_fields = ['dernier_commentaire']
            if hasattr(self.formation, 'saturation_moyenne'):
                update_fields.append('saturation_moyenne')
            if hasattr(self.formation, 'nb_commentaires'):
                update_fields.append('nb_commentaires')
                
            self.formation.save(update_fields=update_fields)

    @staticmethod
    def update_formation_static(formation):
        """
        🔄 Version statique de update_formation.
        Utilisée lors de la suppression d'un commentaire.
        
        Args:
            formation (Formation): La formation à mettre à jour
        """
        # Assurez-vous que cette méthode existe dans votre modèle Formation
        if hasattr(formation, 'update_from_commentaires'):
            formation.update_from_commentaires()
        else:
            # Implémentation de secours similaire à update_formation
            from django.db.models import Avg
            
            # Mise à jour du dernier commentaire
            formation.dernier_commentaire = (
                Commentaire.objects.filter(formation=formation)
                .order_by('-created_at')
                .first()
            )
            
            # Calcul de la saturation moyenne
            saturation_avg = (
                Commentaire.objects.filter(formation=formation, saturation__isnull=False)
                .aggregate(Avg('saturation'))
                .get('saturation__avg')
            )
            
            # Mise à jour de la formation
            if hasattr(formation, 'saturation_moyenne'):
                formation.saturation_moyenne = saturation_avg
                
            # Compter les commentaires
            if hasattr(formation, 'nb_commentaires'):
                formation.nb_commentaires = (
                    Commentaire.objects.filter(formation=formation).count()
                )
                
            # Sauvegarder la formation
            update_fields = ['dernier_commentaire']
            if hasattr(formation, 'saturation_moyenne'):
                update_fields.append('saturation_moyenne')
            if hasattr(formation, 'nb_commentaires'):
                update_fields.append('nb_commentaires')
                
            formation.save(update_fields=update_fields)

    # === Propriétés utiles ===

    @property
    def auteur_nom(self) -> str:
        """
        🔍 Retourne le nom complet de l'auteur ou 'Anonyme' si non renseigné.
        
        Returns:
            str: Nom complet de l'auteur ou "Anonyme"
        """
        if not self.created_by:
            return "Anonyme"
        full = f"{self.created_by.first_name} {self.created_by.last_name}".strip()
        return full or self.created_by.username

    @property
    def date_formatee(self) -> str:
        """
        📅 Retourne la date de création formatée (jour/mois/année).
        
        Returns:
            str: Date formatée (JJ/MM/AAAA)
        """
        return self.created_at.strftime('%d/%m/%Y')

    @property
    def heure_formatee(self) -> str:
        """
        🕒 Retourne l'heure de création formatée (heure:minute).
        
        Returns:
            str: Heure formatée (HH:MM)
        """
        return self.created_at.strftime('%H:%M')
        
    @property 
    def contenu_sans_html(self) -> str:
        """
        🧹 Retourne le contenu nettoyé de tout HTML.
        
        Returns:
            str: Contenu sans HTML
        """
        return strip_tags(self.contenu)

    @property
    def formation_nom(self) -> str:
        """
        🏫 Retourne le nom de la formation associée.
        
        Returns:
            str: Nom de la formation
        """
        return self.formation.nom if self.formation else "Formation inconnue"

    # === Méthodes utilitaires ===

    def get_content_preview(self, length=None) -> str:
        """
        📝 Récupère un aperçu tronqué du contenu du commentaire.

        Args:
            length (int, optional): Nombre de caractères à afficher avant troncature.
                Si None, utilise la valeur par défaut PREVIEW_DEFAULT_LENGTH.

        Returns:
            str: Contenu court avec '...' si nécessaire
        """
        length = length or self.PREVIEW_DEFAULT_LENGTH
        return self.contenu if len(self.contenu) <= length else f"{self.contenu[:length]}..."

    def is_recent(self, days=None) -> bool:
        """
        ⏱️ Indique si le commentaire a été posté récemment.

        Args:
            days (int, optional): Nombre de jours à considérer pour 'récent'.
                Si None, utilise la valeur par défaut RECENT_DEFAULT_DAYS.

        Returns:
            bool: True si récent, sinon False.
        """
        days = days or self.RECENT_DEFAULT_DAYS
        return self.created_at >= timezone.now() - timedelta(days=days)
        
    def is_edited(self) -> bool:
        """
        ✏️ Indique si le commentaire a été modifié après sa création.
        
        Returns:
            bool: True si modifié, False sinon
        """
        # Tolérance de 1 minute entre création et modification
        tolerance = timedelta(minutes=1)
        return self.updated_at and (self.updated_at - self.created_at > tolerance)

    # === Méthodes de classe ===

    @classmethod
    def get_all_commentaires(cls, formation_id=None, auteur_id=None, search_query=None, order_by="-created_at"):
        """
        📊 Récupère dynamiquement les commentaires selon des filtres.

        Args:
            formation_id (int, optional): ID de la formation concernée.
            auteur_id (int, optional): ID de l'auteur.
            search_query (str, optional): Filtre sur le contenu (texte libre).
            order_by (str, optional): Champ de tri, par défaut date décroissante.

        Returns:
            QuerySet: Liste filtrée de commentaires.
        """
        logger.debug(f"Chargement des commentaires filtrés")

        queryset = cls.objects.select_related('formation', 'created_by').order_by(order_by)
        filters = Q()

        if formation_id:
            filters &= Q(formation_id=formation_id)
        if auteur_id:
            filters &= Q(created_by_id=auteur_id)
        if search_query:
            filters &= Q(contenu__icontains=search_query)

        queryset = queryset.filter(filters)
        logger.debug(f"{queryset.count()} commentaire(s) trouvé(s)")
        return queryset if queryset.exists() else cls.objects.none()

    @classmethod
    def get_recent_commentaires(cls, days=None, limit=5):
        """
        📅 Récupère les commentaires récents dans une période donnée.

        Args:
            days (int, optional): Nombre de jours à considérer comme récents.
                Si None, utilise la valeur par défaut RECENT_DEFAULT_DAYS.
            limit (int): Nombre maximum de commentaires à retourner.

        Returns:
            QuerySet: Commentaires récents les plus récents d'abord.
        """
        days = days or cls.RECENT_DEFAULT_DAYS
        date_limite = timezone.now() - timedelta(days=days)
        return cls.objects.select_related('formation', 'created_by')\
            .filter(created_at__gte=date_limite)\
            .order_by('-created_at')[:limit]
            
    @classmethod
    def get_saturation_stats(cls, formation_id=None):
        """
        📊 Récupère des statistiques sur la saturation.
        
        Args:
            formation_id (int, optional): Si fourni, filtre par formation
            
        Returns:
            dict: Statistiques de saturation (moyenne, min, max, count)
        """
        queryset = cls.objects.filter(saturation__isnull=False)
        
        if formation_id:
            queryset = queryset.filter(formation_id=formation_id)
            
        stats = queryset.aggregate(
            avg=Avg('saturation'),
            min=models.Min('saturation'),
            max=models.Max('saturation'),
            count=Count('id')
        )
        
        return stats

    def to_serializable_dict(self, include_full_content=False):
        """
        📦 Retourne une représentation sérialisable du commentaire.

        Args:
            include_full_content (bool): Si True, inclut le contenu complet
                                         sinon, inclut seulement un aperçu

        Returns:
            dict: Dictionnaire des champs exposables du commentaire.
        """
        return {
            "id": self.pk,
            "formation_id": self.formation_id,
            "formation_nom": self.formation.nom,
            "contenu": self.contenu if include_full_content else self.get_content_preview(),
            "saturation": self.saturation,
            "auteur": self.auteur_nom,
            "date": self.date_formatee,
            "heure": self.heure_formatee,
            "is_recent": self.is_recent(),
            "is_edited": self.is_edited(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        
    def get_edit_url(self):
        """
        ✏️ Retourne l'URL vers la vue de modification du commentaire.
        
        Returns:
            str: URL d'édition pour ce commentaire
        """
        return reverse("commentaire-edit", kwargs={"pk": self.pk})
        
    def get_delete_url(self):
        """
        🗑️ Retourne l'URL vers la vue de suppression du commentaire.
        
        Returns:
            str: URL de suppression pour ce commentaire
        """
        return reverse("commentaire-delete", kwargs={"pk": self.pk})


================================================
FILE: rap_app/models/custom_user.py
================================================
import logging
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.functional import cached_property
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.base_user import BaseUserManager

logger = logging.getLogger("rap_app.customuser")


class CustomUserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle CustomUser.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def create_user(self, email, username=None, password=None, **extra_fields):
        """
        Crée et retourne un utilisateur avec un email et mot de passe.
        """
        if not email:
            raise ValueError()
        email = self.normalize_email(email)
        user = self.model(email=email, username=username or email.split('@')[0], **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        """
        Crée et retourne un superutilisateur avec tous les droits.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.ROLE_SUPERADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, username, password, **extra_fields)    
    def active(self):
        """
        Retourne uniquement les utilisateurs actifs.
        
        Returns:
            QuerySet: Utilisateurs actifs
        """
        return self.filter(is_active=True)
    
    def by_role(self, role):
        """
        Filtre les utilisateurs par rôle.
        
        Args:
            role (str): Un des rôles définis dans CustomUser.ROLE_CHOICES
            
        Returns:
            QuerySet: Utilisateurs ayant le rôle spécifié
        """
        return self.filter(role=role)
    
    def admins(self):
        """
        Retourne tous les utilisateurs administrateurs.
        
        Returns:
            QuerySet: Tous les administrateurs et super-administrateurs
        """
        return self.filter(role__in=[CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN])
    
    def create_user_with_role(self, email, username, password, role=None, **extra_fields):
        """
        Crée un nouvel utilisateur avec un rôle spécifique.
        
        Args:
            email (str): Email de l'utilisateur (obligatoire)
            username (str): Nom d'utilisateur
            password (str): Mot de passe
            role (str, optional): Rôle à assigner
            **extra_fields: Champs supplémentaires
            
        Returns:
            CustomUser: Nouvel utilisateur créé
        """
        if not email:
            raise ValueError("L'adresse email est obligatoire")
            
        if role and not any(role == r[0] for r in CustomUser.ROLE_CHOICES):
            raise ValueError(f"Rôle invalide: {role}")
            
        extra_fields.setdefault('is_staff', role in [CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN, CustomUser.ROLE_STAFF])
        extra_fields.setdefault('is_superuser', role == CustomUser.ROLE_SUPERADMIN)
        
        if role:
            extra_fields['role'] = role
            
        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    👤 Modèle utilisateur personnalisé basé sur AbstractUser.

    Remplace le modèle utilisateur par défaut de Django.
    Utilise l'email comme identifiant unique.
    
    Attributs:
        email (str): Adresse email, utilisée comme identifiant de connexion
        phone (str): Numéro de téléphone (optionnel)
        avatar (ImageField): Image de profil (optionnel)
        bio (str): Biographie ou texte de présentation (optionnel)
        role (str): Rôle ou niveau d'accès de l'utilisateur
        
    Propriétés:
        full_name (str): Nom complet (prénom + nom)
        serializable_data (dict): Données sérialisables pour API
        
    Méthodes:
        is_admin(): Vérifie si l'utilisateur est administrateur
        is_staff_or_admin(): Vérifie si l'utilisateur est staff ou admin
        avatar_url(): Retourne l'URL de l'avatar
    """

    # Constantes pour les rôles
    ROLE_SUPERADMIN = 'superadmin'
    ROLE_ADMIN = 'admin'
    ROLE_STAGIAIRE = 'stagiaire'
    ROLE_STAFF = 'staff'
    ROLE_TEST = 'test'

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, "Super administrateur"),
        (ROLE_ADMIN, "Administrateur"),
        (ROLE_STAGIAIRE, "Stagiaire"),
        (ROLE_STAFF, "Membre du staff"),
        (ROLE_TEST, "Test"),
    ]
    
    # Constantes pour validation
    PHONE_MAX_LENGTH = 20
    USERNAME_VALIDATOR = UnicodeUsernameValidator()

    # Champs personnalisés
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse email",
        help_text="Adresse email utilisée pour la connexion",
        error_messages={
            'unique': "Un utilisateur avec cette adresse email existe déjà."
        }
    )

    phone = models.CharField(
        max_length=PHONE_MAX_LENGTH,
        blank=True,
        verbose_name="Téléphone",
        help_text="Numéro de téléphone de l'utilisateur"
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name="Avatar",
        help_text="Image de profil de l'utilisateur"
    )

    bio = models.TextField(
        blank=True,
        verbose_name="Biographie",
        help_text="Texte de présentation ou informations supplémentaires"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAGIAIRE,
        verbose_name="Rôle",
        help_text="Rôle ou niveau d'accès de l'utilisateur",
        db_index=True
    )
    
    # Paramètres d'authentification
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Managers
    objects = CustomUserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        indexes = [
            models.Index(fields=['role'], name='customuser_role_idx'),
            models.Index(fields=['email'], name='customuser_email_idx'),
            models.Index(fields=['is_active'], name='customuser_active_idx'),
        ]
        ordering = ['-date_joined']
        permissions = [
            ("can_view_all_users", "Peut voir tous les utilisateurs"),
            ("can_export_users", "Peut exporter les données utilisateurs"),
        ]



    def clean(self):
        """
        🧪 Validation personnalisée :
        - Vérifie le format du numéro de téléphone
        - S'assure que seul un superuser peut avoir le rôle 'superadmin'
        - Normalise l'email (lowercase) et le rôle (lowercase + strip)
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()

        # Validation du téléphone
        if self.phone:
            phone_cleaned = self.phone.replace('+', '').replace(' ', '').replace('-', '')
            if not phone_cleaned.isdigit():
                raise ValidationError({
                    'phone': "Le numéro de téléphone ne doit contenir que des chiffres, des espaces, un '+' ou des tirets"
                })

        # Normalisation du rôle
        if self.role:
            self.role = self.role.lower().strip()

        # Validation du rôle superadmin
        if self.role == self.ROLE_SUPERADMIN and not self.is_superuser:
            raise ValidationError({
                'role': "Seul un superuser peut avoir le rôle 'Super administrateur'"
            })

        # Normalisation de l'email
        if self.email:
            self.email = self.email.lower().strip()


    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde personnalisée :
        - Normalise l'email, le téléphone et le rôle
        - Met à jour les flags is_staff/is_superuser selon le rôle
        - Effectue la validation
        - Journalise la création ou mise à jour
        """
        is_new = self.pk is None

        # ✅ Normalisation de l'email
        if self.email:
            self.email = self.email.strip().lower()

        # ✅ Normalisation du rôle
        if self.role:
            self.role = self.role.strip().lower()

        # ✅ Normalisation du téléphone
        if self.phone:
            self.phone = ' '.join(self.phone.split())

        # 🔁 Synchronisation des flags selon le rôle
        if self.role == self.ROLE_SUPERADMIN:
            self.is_superuser = True
            self.is_staff = True
        elif self.role in [self.ROLE_ADMIN, self.ROLE_STAFF]:
            self.is_staff = True

        # ✅ Validation avant sauvegarde
        try:
            self.full_clean()
        except ValidationError as e:
            logger.error(f"Erreur de validation pour l'utilisateur {self.email}: {e}")
            raise

        # ✅ Sauvegarde réelle
        super().save(*args, **kwargs)

        # 📝 Journalisation
        if is_new:
            logger.info(f"✅ Utilisateur créé : {self.email} avec rôle {self.get_role_display()}")
        else:
            logger.info(f"🔄 Utilisateur mis à jour : {self.email}")

    def __str__(self):
        """🔁 Représentation textuelle de l'utilisateur."""
        return f"{self.get_full_name()} ({self.email})"
        
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<CustomUser(id={self.pk}, email='{self.email}', role='{self.role}')>"

    def get_full_name(self):
        """
        📛 Nom complet de l'utilisateur.

        Returns:
            str: Prénom + Nom ou username/email
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email
        
    @property
    def full_name(self):
        """
        Alias de get_full_name pour utilisation comme propriété.
        
        Returns:
            str: Nom complet de l'utilisateur
        """
        return self.get_full_name()

    def avatar_url(self):
        """
        🖼️ Retourne l'URL de l'avatar ou une image par défaut.
        
        Returns:
            str: URL de l'avatar ou image par défaut
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default_avatar.png'

        
    def get_admin_url(self):
        """
        🔗 URL vers la page d'administration de l'utilisateur.
        
        Returns:
            str: URL d'administration
        """
        from django.urls import reverse
        return reverse('admin:auth_user_change', args=[self.pk])

    def to_serializable_dict(self, include_sensitive=False):
        """
        📦 Retourne une représentation sérialisable de l'utilisateur.
        
        Args:
            include_sensitive (bool): Si True, inclut des données plus sensibles
            
        Returns:
            dict: Données sérialisables
        """
        base_data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'avatar_url': self.avatar_url(),
            'role': self.role,
            'role_display': self.get_role_display(),
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
            'is_active': self.is_active,
        }
        
        # Ajouter les données optionnelles selon le niveau d'accès
        if include_sensitive:
            base_data.update({
                'phone': self.phone,
                'bio': self.bio,
                'is_staff': self.is_staff,
                'is_superuser': self.is_superuser,
                'last_login': self.last_login.isoformat() if self.last_login else None,
            })
            
        return base_data

    @property
    def serializable_data(self):
        """
        📦 Propriété pour la rétrocompatibilité.
        Équivalent à to_serializable_dict(include_sensitive=True).

        Returns:
            dict: Données de l'utilisateur prêtes pour une API
        """
        return self.to_serializable_dict(include_sensitive=True)
        
    @cached_property
    def permissions_list(self):
        """
        🔐 Liste des permissions de l'utilisateur.
        Mise en cache pour optimiser les performances.
        
        Returns:
            list: Liste des codenames de permission
        """
        if self.is_superuser:
            from django.contrib.auth.models import Permission
            return list(Permission.objects.values_list('codename', flat=True))
            
        return list(self.user_permissions.values_list('codename', flat=True))

    # 🔐 Helpers de rôle - avec validation stricte des types
    def is_admin(self):
        """
        Vérifie si l'utilisateur a un rôle d'administrateur.
        
        Returns:
            bool: True si admin ou superadmin
        """
        return self.role in [self.ROLE_ADMIN, self.ROLE_SUPERADMIN]

    def is_staff_or_admin(self):
        """
        Vérifie si l'utilisateur est staff ou administrateur.
        
        Returns:
            bool: True si staff, admin ou superadmin
        """
        return self.role in [self.ROLE_STAFF, self.ROLE_ADMIN, self.ROLE_SUPERADMIN]

    def is_stagiaire(self):
        """
        Vérifie si l'utilisateur est un stagiaire.
        
        Returns:
            bool: True si stagiaire
        """
        return self.role == self.ROLE_STAGIAIRE

    def is_superadmin(self):
        """
        Vérifie si l'utilisateur est super-administrateur.
        
        Returns:
            bool: True si superadmin
        """
        return self.role == self.ROLE_SUPERADMIN

    def is_staff_custom(self):
        """
        Vérifie si l'utilisateur est membre du staff.
        
        Returns:
            bool: True si staff
        """
        return self.role == self.ROLE_STAFF

    def is_test(self):
        """
        Vérifie si c'est un compte de test.
        
        Returns:
            bool: True si compte test
        """
        return self.role == self.ROLE_TEST
        
    def has_module_access(self, module_name):
        """
        Vérifie si l'utilisateur a accès à un module spécifique.
        À implémenter selon vos besoins métier.
        
        Args:
            module_name (str): Nom du module à vérifier
            
        Returns:
            bool: True si l'utilisateur a accès
        """
        # Exemple - à adapter selon votre logique d'accès
        if self.is_superadmin():
            return True
            
        # Implémentez votre logique d'accès aux modules ici
        module_access = {
            'admin': [self.ROLE_ADMIN, self.ROLE_SUPERADMIN],
            'reporting': [self.ROLE_ADMIN, self.ROLE_SUPERADMIN, self.ROLE_STAFF],
            'formation': [self.ROLE_ADMIN, self.ROLE_SUPERADMIN, self.ROLE_STAFF, self.ROLE_STAGIAIRE],
        }
        
        return module_name in module_access and self.role in module_access[module_name]
        
    @classmethod
    def get_role_choices_display(cls):
        """
        Retourne un dictionnaire des rôles et leurs labels.
        Utile pour les formulaires ou l'API.
        
        Returns:
            dict: Dictionnaire {code_role: label}
        """
        return dict(cls.ROLE_CHOICES)
        
    @classmethod
    def get_csv_fields(cls):
        """
        Définit les champs à inclure dans un export CSV.
        
        Returns:
            list: Liste des noms de champs
        """
        return [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'role', 'date_joined', 'is_active'
        ]
        
    @classmethod
    def get_csv_headers(cls):
        """
        Définit les en-têtes pour un export CSV.
        
        Returns:
            list: Liste des en-têtes de colonnes
        """
        return [
            'ID', 'Email', 'Nom d\'utilisateur', 'Prénom', 'Nom',
            'Rôle', 'Date d\'inscription', 'Actif'
        ]


================================================
FILE: rap_app/models/documents.py
================================================
import os
import magic
import logging
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.conf import settings
from django.urls import reverse
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property

from .base import BaseModel
from .formations import Formation
from .formations import HistoriqueFormation  # nécessaire pour le logging historique

logger = logging.getLogger("application.documents")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------

class DocumentManager(models.Manager):
    """
    Manager personnalisé pour le modèle Document.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def by_type(self, type_doc):
        """
        Retourne les documents filtrés par type.
        
        Args:
            type_doc (str): Type de document (PDF, IMAGE, etc.)
            
        Returns:
            QuerySet: Documents du type spécifié
        """
        return self.filter(type_document=type_doc)
    
    def for_formation(self, formation_id):
        """
        Retourne les documents d'une formation.
        
        Args:
            formation_id (int): ID de la formation
            
        Returns:
            QuerySet: Documents liés à la formation
        """
        return self.filter(formation_id=formation_id)
    
    def pdfs(self):
        """
        Raccourci pour récupérer tous les documents PDF.
        
        Returns:
            QuerySet: Tous les documents de type PDF
        """
        return self.filter(type_document=Document.PDF)
    
    def images(self):
        """
        Raccourci pour récupérer toutes les images.
        
        Returns:
            QuerySet: Tous les documents de type IMAGE
        """
        return self.filter(type_document=Document.IMAGE)
    
    def contrats(self):
        """
        Raccourci pour récupérer tous les contrats.
        
        Returns:
            QuerySet: Tous les documents de type CONTRAT
        """
        return self.filter(type_document=Document.CONTRAT)
    
    def with_mime_and_size(self):
        """
        Pré-filtre les documents avec MIME et taille.
        Utile pour les listes de documents.
        
        Returns:
            QuerySet: Documents avec informations complètes
        """
        return self.exclude(mime_type__isnull=True).exclude(taille_fichier__isnull=True)


# ===============================
# ✅ Validation d'extension
# ===============================
def validate_file_extension(value, type_doc=None):
    """
    ✅ Valide l'extension d'un fichier selon son type de document.

    Args:
        value (File): Le fichier à valider.
        type_doc (str): Le type de document défini dans les choix.

    Raises:
        ValidationError: Si l'extension est invalide pour ce type.
    """
    ext = os.path.splitext(value.name)[1].lower()
    valides = {
        Document.PDF: ['.pdf'],
        Document.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        Document.CONTRAT: ['.pdf', '.doc', '.docx'],
        Document.AUTRE: []
    }

    if not type_doc or type_doc == Document.AUTRE:
        return

    if ext not in valides.get(type_doc, []):
        raise ValidationError(
            f"Extension invalide pour {type_doc}. "
            f"Attendu : {', '.join(valides.get(type_doc))}"
        )

def filepath_for_document(instance, filename):
    """
    Détermine le chemin de sauvegarde pour un document.
    Organise les fichiers par type et par formation.
    
    Args:
        instance (Document): Instance du document
        filename (str): Nom du fichier original
        
    Returns:
        str: Chemin relatif pour le stockage du fichier
    """
    # Sécuriser le nom de fichier
    base_name, ext = os.path.splitext(filename)
    safe_name = "".join([c for c in base_name if c.isalnum() or c in ' ._-']).strip()
    safe_name = safe_name.replace(' ', '_')
    
    # Chemin avec type de document et ID formation
    formation_id = getattr(instance.formation, 'id', 'unknown')
    return f'formations/documents/{instance.type_document}/{formation_id}/{safe_name}{ext}'


# ===============================
# 📎 Modèle Document
# ===============================
class Document(BaseModel):
    """
    📎 Modèle représentant un document lié à une formation.

    Permet de stocker et valider des fichiers (PDF, images, contrats),
    tout en enregistrant leur ajout dans l'historique de la formation.
    
    Attributs:
        formation (Formation): Formation à laquelle ce document est rattaché
        nom_fichier (str): Nom lisible du fichier
        fichier (FileField): Fichier téléversé
        type_document (str): Type de document (PDF, IMAGE, CONTRAT, AUTRE)
        source (str, optional): Provenance du document
        taille_fichier (int, optional): Taille du fichier en kilo-octets
        mime_type (str, optional): Type MIME détecté automatiquement
        
    Propriétés:
        extension (str): Extension du fichier sans point
        icon_class (str): Classe CSS pour l'icône selon le type
        human_size (str): Taille du fichier formatée en Ko/Mo
        
    Méthodes:
        get_download_url(): URL de téléchargement du fichier
        (): URL vers la page de détail du document
        to_serializable_dict(): Représentation JSON du document
    """

    # === Constantes de type de document ===
    PDF = 'pdf'
    IMAGE = 'image'
    CONTRAT = 'contrat'
    AUTRE = 'autre'

    TYPE_DOCUMENT_CHOICES = [
        (PDF, 'PDF'),
        (IMAGE, 'Image'),
        (CONTRAT, 'Contrat signé'),
        (AUTRE, 'Autre'),
    ]
    
    # Constantes pour les valeurs max
    MAX_FILENAME_LENGTH = 255
    MAX_FILE_SIZE_KB = 10 * 1024  # 10 Mo
    MAX_MIME_LENGTH = 100

    # === Champs principaux ===
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Formation associée"),
        help_text=_("Formation à laquelle ce document est rattaché")
    )

    nom_fichier = models.CharField(
        max_length=MAX_FILENAME_LENGTH,
        db_index=True,
        verbose_name=_("Nom du fichier"),
        help_text=_("Nom lisible du fichier (sera nettoyé automatiquement)")
    )

    fichier = models.FileField(
        upload_to=filepath_for_document,
        verbose_name=_("Fichier"),
        help_text=_(f"Fichier à téléverser (PDF, image, etc.). Max : {MAX_FILE_SIZE_KB//1024} Mo")
    )

    type_document = models.CharField(
        max_length=20,
        choices=TYPE_DOCUMENT_CHOICES,
        default=AUTRE,
        db_index=True,
        verbose_name=_("Type de document"),
        help_text=_("Catégorie du document selon son usage ou son format")
    )

    source = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Source"),
        help_text=_("Texte optionnel indiquant la provenance du document")
    )

    taille_fichier = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Taille (Ko)"),
        help_text=_("Taille du fichier en kilo-octets (calculée automatiquement)")
    )

    mime_type = models.CharField(
        max_length=MAX_MIME_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Type MIME"),
        help_text=_("Type MIME détecté automatiquement (ex : application/pdf)")
    )
    
    # Managers
    objects = models.Manager()
    custom = DocumentManager()

    # === Meta ===
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['nom_fichier'], name='doc_filename_idx'),
            models.Index(fields=['formation'], name='doc_formation_idx'),
            models.Index(fields=['type_document'], name='doc_type_idx'),
            models.Index(fields=['created_at'], name='doc_created_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(nom_fichier__isnull=False) & ~models.Q(nom_fichier=''),
                name='doc_filename_not_empty'
            )
        ]

    # === Représentation ===
    def __str__(self):
        """Représentation textuelle du document."""
        max_length = 50
        nom = self.nom_fichier[:max_length]
        return f"{nom}{'...' if len(self.nom_fichier) > max_length else ''} ({self.get_type_document_display()})"
    
    def __repr__(self):
        """Représentation technique pour le débogage."""
        return f"<Document(id={self.pk}, type='{self.type_document}', formation_id={self.formation_id})>"


    def get_file_extension(self):
        """📎 Retourne l'extension du fichier (ex: '.pdf')."""
        return os.path.splitext(self.fichier.name)[1].lower() if self.fichier else ""

    def get_icon_class(self):
        """🎨 Classe FontAwesome correspondant au type de document."""
        return {
            self.PDF: "fa-file-pdf",
            self.IMAGE: "fa-file-image",
            self.CONTRAT: "fa-file-contract",
            self.AUTRE: "fa-file",
        }.get(self.type_document, "fa-file")
        
    @property
    def icon_class(self):
        """Propriété pour l'icône CSS."""
        return self.get_icon_class()

    def get_download_url(self):
        """🔗 URL de téléchargement du fichier."""
        return self.fichier.url if self.fichier else None

    @property
    def extension(self):
        """🧩 Extension du fichier sans point (ex: 'pdf')."""
        return self.get_file_extension().replace('.', '')
        
    @property
    def human_size(self):
        """
        Retourne la taille du fichier dans un format lisible.
        
        Returns:
            str: Taille du fichier formatée (ex: "512 Ko", "2.5 Mo")
        """
        if not self.taille_fichier:
            return "Inconnu"
            
        if self.taille_fichier < 1024:
            return f"{self.taille_fichier} Ko"
        else:
            return f"{self.taille_fichier/1024:.1f} Mo"
    
    @cached_property
    def is_viewable_in_browser(self):
        """
        Indique si le document peut être affiché dans le navigateur.
        
        Returns:
            bool: True si le document est un PDF ou une image
        """
        return (
            self.type_document in [self.PDF, self.IMAGE] or
            (self.mime_type and (
                self.mime_type.startswith('image/') or 
                self.mime_type == 'application/pdf'
            ))
        )

    def to_serializable_dict(self):
        """📦 Dictionnaire JSON/API du document."""
        return {
            "id": self.pk,
            "nom_fichier": self.nom_fichier,
            "type_document": self.type_document,
            "type_document_display": self.get_type_document_display(),
            "taille_fichier": self.taille_fichier,
            "taille_readable": self.human_size,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "icon_class": self.get_icon_class(),
            "download_url": self.get_download_url(),
            "formation_id": self.formation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
        }

    def clean(self):
        """
        🧹 Nettoyage et validation :
        - Extension valide
        - Taille max
        - Nom échappé
        - Type MIME détecté
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()

        # Validation du nom de fichier
        if not self.nom_fichier or not self.nom_fichier.strip():
            raise ValidationError({"nom_fichier": "Le nom du fichier ne peut pas être vide."})
        
        self.nom_fichier = escape(self.nom_fichier.strip())

        # Validation du fichier
        if self.fichier:
            # Validation de l'extension selon le type
            validate_file_extension(self.fichier, self.type_document)

            # Détection du MIME type
            try:
                self.mime_type = magic.from_buffer(self.fichier.read(2048), mime=True)
                self.fichier.seek(0)
            except Exception as e:
                logger.warning(f"Impossible de détecter le MIME type pour {self.nom_fichier}: {e}")
                # Ne pas bloquer la validation si la détection échoue

            # Validation de la taille
            try:
                taille_ko = self.fichier.size // 1024
                if taille_ko > self.MAX_FILE_SIZE_KB:
                    raise ValidationError({
                        "fichier": f"Le fichier est trop volumineux (max. {self.MAX_FILE_SIZE_KB//1024} Mo)."
                    })
                self.taille_fichier = max(1, taille_ko)  # Au moins 1 Ko pour éviter les 0
            except AttributeError:
                # Si size n'est pas disponible, on ne bloque pas
                pass

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde le document :
        - Validation complète (`clean`)
        - Calcul taille fichier
        - HistoriqueFormation (si nouveau)
        - Log d'ajout
        
        Args:
            *args: Arguments positionnels pour super().save()
            **kwargs: Arguments nommés pour super().save()
            skip_history (bool, optional): Si True, ne pas créer d'historique
        """
        # Extraire le paramètre skip_history
        skip_history = kwargs.pop('skip_history', False)
        
        is_new = self.pk is None
        
        # Valider les données
        self.full_clean()

        # Calculer la taille si non définie
        if not self.taille_fichier and self.fichier and hasattr(self.fichier, 'size'):
            self.taille_fichier = max(1, self.fichier.size // 1024)

        # Sauvegarder
        super().save(*args, **kwargs)

        # Créer un enregistrement dans l'historique si c'est un nouveau document
        if is_new and self.formation and not skip_history:
            try:
                HistoriqueFormation.objects.create(
                    formation=self.formation,
                    champ_modifie="document",
                    ancienne_valeur="—",
                    nouvelle_valeur=self.nom_fichier,
                    commentaire=f"Ajout du document « {self.nom_fichier} »",
                    created_by=self.created_by
                )
                logger.info(f"[Document] Document ajouté : {self.nom_fichier} (formation #{self.formation_id})")
            except Exception as e:
                logger.error(f"[Document] Erreur lors de la création de l'historique : {e}")
                # Ne pas bloquer la sauvegarde si l'historique échoue
    
    def delete(self, *args, **kwargs):
        """
        🗑️ Supprime le document avec journalisation et historique.
        
        Args:
            *args: Arguments positionnels pour super().delete()
            **kwargs: Arguments nommés pour super().delete(), y compris user
            skip_history (bool, optional): Si True, ne pas créer d'historique
        """
        # Extraire les paramètres personnalisés
        skip_history = kwargs.pop('skip_history', False)
        user = kwargs.pop('user', None) or getattr(self, 'created_by', None)
        
        # Garder une référence à la formation et au nom avant suppression
        formation = self.formation
        nom_fichier = self.nom_fichier
        
        # Supprimer le document
        result = super().delete(*args, **kwargs)
        
        # Créer un enregistrement dans l'historique
        if formation and not skip_history:
            try:
                HistoriqueFormation.objects.create(
                    formation=formation,
                    champ_modifie="document",
                    ancienne_valeur=nom_fichier,
                    nouvelle_valeur="—",
                    commentaire=f"Suppression du document « {nom_fichier} »",
                    created_by=user
                )
                logger.info(f"[Document] Document supprimé : {nom_fichier} (formation #{formation.id})")
            except Exception as e:
                logger.error(f"[Document] Erreur lors de la création de l'historique de suppression : {e}")
        
        return result
    
    @classmethod
    def get_extensions_by_type(cls, type_doc=None):
        """
        Retourne les extensions valides pour un type de document.
        
        Args:
            type_doc (str, optional): Type de document, ou None pour tous
            
        Returns:
            dict: Dictionnaire des extensions valides par type
        """
        extensions = {
            cls.PDF: ['.pdf'],
            cls.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            cls.CONTRAT: ['.pdf', '.doc', '.docx'],
            cls.AUTRE: []
        }
        
        if type_doc:
            return {type_doc: extensions.get(type_doc, [])}
        return extensions
        
    @classmethod
    def get_mime_types_by_type(cls, type_doc=None):
        """
        Retourne les types MIME valides pour un type de document.
        
        Args:
            type_doc (str, optional): Type de document, ou None pour tous
            
        Returns:
            dict: Dictionnaire des types MIME valides par type
        """
        mime_types = {
            cls.PDF: ['application/pdf'],
            cls.IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            cls.CONTRAT: ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            cls.AUTRE: []
        }
        
        if type_doc:
            return {type_doc: mime_types.get(type_doc, [])}
        return mime_types
    
    @classmethod
    def get_by_formation_and_type(cls, formation_id, type_doc=None):
        """
        Récupère les documents d'une formation filtrés par type.
        
        Args:
            formation_id (int): ID de la formation
            type_doc (str, optional): Type de document, ou None pour tous
            
        Returns:
            QuerySet: Documents filtrés
        """
        queryset = cls.objects.filter(formation_id=formation_id)
        
        if type_doc:
            queryset = queryset.filter(type_document=type_doc)
            
        return queryset.order_by('-created_at')


================================================
FILE: rap_app/models/evenements.py
================================================
import logging
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.db.models import Q, F, Avg, Count, Sum

from .base import BaseModel
from .formations import Formation

logger = logging.getLogger("application.evenements")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


class EvenementManager(models.Manager):
    """
    Manager personnalisé pour le modèle Evenement.
    Fournit des méthodes utilitaires pour les requêtes courantes.
    """
    
    def a_venir(self, days=30):
        """
        Retourne les événements à venir dans les prochains jours.
        
        Args:
            days (int): Nombre de jours à considérer
            
        Returns:
            QuerySet: Événements à venir
        """
        today = timezone.now().date()
        limit_date = today + timezone.timedelta(days=days)
        return self.filter(
            event_date__gte=today,
            event_date__lte=limit_date
        ).order_by('event_date')
    
    def passes(self):
        """
        Retourne les événements déjà passés.
        
        Returns:
            QuerySet: Événements passés
        """
        today = timezone.now().date()
        return self.filter(event_date__lt=today).order_by('-event_date')
    
    def aujourd_hui(self):
        """
        Retourne les événements ayant lieu aujourd'hui.
        
        Returns:
            QuerySet: Événements du jour
        """
        today = timezone.now().date()
        return self.filter(event_date=today)
    
    def par_type(self, type_evenement):
        """
        Filtre les événements par type.
        
        Args:
            type_evenement (str): Type d'événement (utiliser les constantes TypeEvenement)
            
        Returns:
            QuerySet: Événements filtrés par type
        """
        return self.filter(type_evenement=type_evenement)
    
    def par_formation(self, formation_id):
        """
        Filtre les événements par formation.
        
        Args:
            formation_id (int): ID de la formation
            
        Returns:
            QuerySet: Événements liés à la formation
        """
        return self.filter(formation_id=formation_id)
    
    def avec_statistiques(self):
        """
        Ajoute des statistiques calculées aux événements.
        
        Returns:
            QuerySet: Événements avec des annotations
        """
        return self.annotate(
            taux_participation=models.Case(
                models.When(
                    participants_prevus__gt=0,
                    then=models.ExpressionWrapper(
                        100 * F('participants_reels') / F('participants_prevus'),
                        output_field=models.FloatField()
                    )
                ),
                default=None,
                output_field=models.FloatField()
            )
        )


class Evenement(BaseModel):
    """
    📅 Modèle représentant un événement lié à une formation (job dating, forum, etc.).
    
    Permet de suivre les types d'événements, leur date, lieu, et le nombre de participants.
    
    Attributs:
        formation (Formation): Formation associée à l'événement (optionnel)
        type_evenement (str): Type d'événement selon les choix prédéfinis
        description_autre (str): Description personnalisée pour le type 'Autre'
        details (str): Détails ou informations supplémentaires
        event_date (date): Date de l'événement
        lieu (str): Lieu où se déroule l'événement
        participants_prevus (int): Nombre de participants attendus
        participants_reels (int): Nombre de participants effectifs
        
    Propriétés:
        status_label (str): Statut textuel (Passé, Aujourd'hui, À venir)
        status_color (str): Classe CSS pour la couleur du statut
        
    Méthodes:
        get_temporal_status(): Calcule le statut temporel (past, today, soon, future)
        get_participation_rate(): Calcule le taux de participation si possible
        to_serializable_dict(): Représentation sérialisable pour API
    """
    
    # Constantes pour les limites de champs
    MAX_TYPE_LENGTH = 100
    MAX_DESC_LENGTH = 255
    MAX_LIEU_LENGTH = 255
    DAYS_SOON = 7  # Nombre de jours pour considérer un événement comme "bientôt"
    
    # ===== Choix de types d'événements =====
    class TypeEvenement(models.TextChoices):
        INFO_PRESENTIEL = 'info_collective_presentiel', _('Information collective présentiel')
        INFO_DISTANCIEL = 'info_collective_distanciel', _('Information collective distanciel')
        JOB_DATING = 'job_dating', _('Job dating')
        EVENEMENT_EMPLOI = 'evenement_emploi', _('Événement emploi')
        FORUM = 'forum', _('Forum')
        JPO = 'jpo', _('Journée Portes Ouvertes')
        AUTRE = 'autre', _('Autre')
    
    # ===== Statuts temporels =====
    class StatutTemporel(models.TextChoices):
        PASSE = 'past', _('Passé')
        AUJOURD_HUI = 'today', _('Aujourd\'hui')
        BIENTOT = 'soon', _('Bientôt')
        FUTUR = 'future', _('À venir')
        INCONNU = 'unknown', _('Inconnu')

    # ===== Champs du modèle =====
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="evenements",
        verbose_name=_("Formation"),
        help_text=_("Formation associée à l'événement")
    )

    type_evenement = models.CharField(
        max_length=MAX_TYPE_LENGTH,
        choices=TypeEvenement.choices,
        db_index=True,
        verbose_name=_("Type d'événement"),
        help_text=_("Catégorie de l'événement (ex : forum, job dating, etc.)")
    )

    description_autre = models.CharField(
        max_length=MAX_DESC_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Description personnalisée"),
        help_text=_("Détail du type si 'Autre' est sélectionné")
    )

    details = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Détails complémentaires"),
        help_text=_("Détails ou informations supplémentaires")
    )

    event_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de l'événement"),
        help_text=_("Date prévue pour l'événement")
    )

    lieu = models.CharField(
        max_length=MAX_LIEU_LENGTH,
        blank=True,
        null=True,
        verbose_name=_("Lieu"),
        help_text=_("Lieu où se déroule l'événement")
    )

    participants_prevus = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Participants prévus"),
        help_text=_("Nombre de personnes attendues")
    )

    participants_reels = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Participants réels"),
        help_text=_("Nombre de participants présents")
    )
    
    # ===== Managers =====
    objects = models.Manager()
    custom = EvenementManager()

    # ===== Meta =====
    class Meta:
        verbose_name = _("Événement")
        verbose_name_plural = _("Événements")
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['event_date'], name='event_date_idx'),
            models.Index(fields=['type_evenement'], name='event_type_idx'),
            models.Index(fields=['formation'], name='event_formation_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(type_evenement='autre', description_autre__isnull=False) | ~Q(type_evenement='autre'),
                name='autre_needs_description'
            )
        ]

    # ===== Représentation =====
    def __str__(self):
        """Représentation textuelle de l'événement."""
        label = self.description_autre if self.type_evenement == self.TypeEvenement.AUTRE and self.description_autre else self.get_type_evenement_display()
        date_str = self.event_date.strftime('%d/%m/%Y') if self.event_date else "Date inconnue"
        return f"{label} - {date_str} - {self.status_label}"
    
    def __repr__(self):
        """Représentation pour le débogage."""
        return f"<Evenement(id={self.pk}, type='{self.type_evenement}', date='{self.event_date}')>"

    
    def get_edit_url(self):
        """
        🔗 Retourne l'URL de modification de l'événement.
        
        Returns:
            str: URL de la page d'édition
        """
        return reverse("evenement-edit", kwargs={"pk": self.pk})
    
    def get_delete_url(self):
        """
        🔗 Retourne l'URL de suppression de l'événement.
        
        Returns:
            str: URL de la page de suppression
        """
        return reverse("evenement-delete", kwargs={"pk": self.pk})

    # ===== Sérialisation =====
    def to_serializable_dict(self):
        """
        📦 Retourne une représentation sérialisable pour API.
        
        Returns:
            dict: Données sérialisables de l'événement
        """
        return {
            "id": self.pk,
            "formation_id": self.formation_id,
            "formation_nom": self.formation.nom if self.formation else None,
            "type_evenement": self.type_evenement,
            "type_evenement_display": self.get_type_evenement_display(),
            "description_autre": self.description_autre,
            "details": self.details,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "event_date_formatted": self.event_date.strftime('%d/%m/%Y') if self.event_date else None,
            "lieu": self.lieu,
            "participants_prevus": self.participants_prevus,
            "participants_reels": self.participants_reels,
            "taux_participation": self.get_participation_rate(),
            "status": self.get_temporal_status(),
            "status_label": self.status_label,
            "status_color": self.status_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ===== Validation =====
    def clean(self):
        """
        Validation des données avant sauvegarde.
        
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        super().clean()
        
        today = timezone.now().date()
        
        # Validation type "Autre"
        if self.type_evenement == self.TypeEvenement.AUTRE and not self.description_autre:
            raise ValidationError({
                'description_autre': _("Veuillez décrire l'événement de type 'Autre'.")
            })
        
        # Validation de date ancienne (warning uniquement)
        if self.event_date and self.event_date < today - timezone.timedelta(days=365):
            logger.warning(f"Date ancienne pour l'événement #{self.pk} : {self.event_date}")
        
        # Validation participants
        if self.participants_reels is not None and self.participants_prevus:
            if self.participants_reels > self.participants_prevus * 1.5:
                logger.warning(f"Participants réels ({self.participants_reels}) dépassent largement les prévisions ({self.participants_prevus}) pour l'événement #{self.pk}")
                
            if self.participants_reels == 0 and self.get_temporal_status() == self.StatutTemporel.PASSE:
                logger.warning(f"Événement passé #{self.pk} avec 0 participant réel")

    # ===== Sauvegarde =====
    def save(self, *args, **kwargs):
        """
        💾 Sauvegarde l'événement avec nettoyage, validation, et journalisation des modifications.

        - Valide les champs (`full_clean`)
        - Utilise `transaction.atomic` pour la cohérence
        - Logue les différences si modification détectée
        - Permet le suivi utilisateur via `user=...` dans `kwargs`
        
        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés, notamment user
        """
        user = kwargs.pop("user", None)
        is_new = self.pk is None
        original = None if is_new else self.__class__.objects.filter(pk=self.pk).first()

        # Validation des données
        self.full_clean()

        with transaction.atomic():
            # Sauvegarde
            super().save(*args, user=user, **kwargs)
            
            # Journalisation
            if is_new:
                logger.info(f"Nouvel événement '{self}' créé (ID: {self.pk}).")
            elif original:
                self._log_changes(original)

    def _log_changes(self, original):
        """
        📝 Enregistre les modifications détectées par comparaison avec l'instance originale.

        Args:
            original (Evenement): Ancienne version de l'objet avant modification.
        """
        # Liste des champs à surveiller
        fields_to_watch = [
            ('type_evenement', 'Type d\'événement'),
            ('event_date', 'Date'),
            ('formation_id', 'Formation'),
            ('lieu', 'Lieu'),
            ('participants_prevus', 'Participants prévus'),
            ('participants_reels', 'Participants réels'),
            ('description_autre', 'Description personnalisée'),
        ]
        
        # Détection des changements
        changes = []
        for field, label in fields_to_watch:
            old_value = getattr(original, field)
            new_value = getattr(self, field)
            
            if old_value != new_value:
                old_display = self._format_field_value(field, old_value)
                new_display = self._format_field_value(field, new_value)
                changes.append(f"{label}: '{old_display}' → '{new_display}'")
        
        # Journalisation si des changements sont détectés
        if changes:
            logger.info(f"Modification de l'événement #{self.pk} : {', '.join(changes)}")
    
    def _format_field_value(self, field_name, value):
        """
        Formate une valeur de champ pour l'affichage dans les logs.
        
        Args:
            field_name (str): Nom du champ
            value: Valeur à formater
            
        Returns:
            str: Valeur formatée
        """
        if value is None:
            return "Non défini"
            
        if field_name == 'event_date' and value:
            return value.strftime('%d/%m/%Y')
            
        if field_name == 'type_evenement':
            return dict(self.TypeEvenement.choices).get(value, value)
            
        if field_name == 'formation_id' and value:
            try:
                formation = Formation.objects.get(pk=value)
                return formation.nom
            except Formation.DoesNotExist:
                return f"Formation #{value}"
                
        return str(value)

    # ===== Status temporel =====
    def get_temporal_status(self, days=None):
        """
        🧭 Retourne le statut temporel de l'événement.
        
        Args:
            days (int, optional): Jours à considérer pour "bientôt"
                Si None, utilise la valeur par défaut DAYS_SOON
        
        Returns:
            str: Statut temporel (past, today, soon, future, unknown)
        """
        days = days or self.DAYS_SOON
        
        if not self.event_date:
            return self.StatutTemporel.INCONNU
            
        today = timezone.now().date()
        
        if self.event_date < today:
            return self.StatutTemporel.PASSE
            
        if self.event_date == today:
            return self.StatutTemporel.AUJOURD_HUI
            
        if self.event_date <= today + timezone.timedelta(days=days):
            return self.StatutTemporel.BIENTOT
            
        return self.StatutTemporel.FUTUR

    @property
    def status_label(self):
        """
        Libellé du statut temporel, adapté pour l'affichage.
        
        Returns:
            str: Libellé du statut (Passé, Aujourd'hui, À venir, etc.)
        """
        return {
            self.StatutTemporel.PASSE: _("Passé"),
            self.StatutTemporel.AUJOURD_HUI: _("Aujourd'hui"),
            self.StatutTemporel.BIENTOT: _("Bientôt"),
            self.StatutTemporel.FUTUR: _("À venir"),
            self.StatutTemporel.INCONNU: _("Date inconnue"),
        }.get(self.get_temporal_status(), _("Inconnu"))

    @property
    def status_color(self):
        """
        Classe CSS pour la couleur du statut.
        
        Returns:
            str: Classe CSS Bootstrap (text-*)
        """
        return {
            self.StatutTemporel.PASSE: "text-secondary",
            self.StatutTemporel.AUJOURD_HUI: "text-danger",
            self.StatutTemporel.BIENTOT: "text-warning",
            self.StatutTemporel.FUTUR: "text-primary",
            self.StatutTemporel.INCONNU: "text-muted",
        }.get(self.get_temporal_status(), "text-muted")
    
    @property
    def status_badge_class(self):
        """
        Classe CSS pour un badge de statut.
        
        Returns:
            str: Classe CSS Bootstrap (badge-*)
        """
        return {
            self.StatutTemporel.PASSE: "badge-secondary",
            self.StatutTemporel.AUJOURD_HUI: "badge-danger",
            self.StatutTemporel.BIENTOT: "badge-warning",
            self.StatutTemporel.FUTUR: "badge-primary",
            self.StatutTemporel.INCONNU: "badge-light",
        }.get(self.get_temporal_status(), "badge-light")
    
    @property
    def is_past(self):
        """
        Indique si l'événement est passé.
        
        Returns:
            bool: True si l'événement est passé
        """
        return self.get_temporal_status() == self.StatutTemporel.PASSE
    
    @property
    def is_today(self):
        """
        Indique si l'événement a lieu aujourd'hui.
        
        Returns:
            bool: True si l'événement est aujourd'hui
        """
        return self.get_temporal_status() == self.StatutTemporel.AUJOURD_HUI
    
    @property
    def is_future(self):
        """
        Indique si l'événement est à venir.
        
        Returns:
            bool: True si l'événement est à venir
        """
        status = self.get_temporal_status()
        return status in [self.StatutTemporel.BIENTOT, self.StatutTemporel.FUTUR]

    # ===== Statistiques =====
    def get_participation_rate(self):
        """
        📊 Calcule le taux de participation si possible.
        
        Returns:
            float: Taux de participation en pourcentage, ou None
        """
        if self.participants_prevus and self.participants_reels is not None and self.participants_prevus > 0:
            return round((self.participants_reels / self.participants_prevus) * 100, 1)
        return None
    
    @property
    def taux_participation(self):
        """Alias pour get_participation_rate."""
        return self.get_participation_rate()
    
    @property
    def taux_participation_formatted(self):
        """
        Taux de participation formaté pour l'affichage.
        
        Returns:
            str: Taux formaté avec % ou "N/A"
        """
        taux = self.get_participation_rate()
        return f"{taux}%" if taux is not None else "N/A"
    
    @cached_property
    def participation_status(self):
        """
        Évalue le niveau de participation.
        
        Returns:
            str: 'success', 'warning', 'danger' ou 'neutral'
        """
        taux = self.get_participation_rate()
        if taux is None:
            return 'neutral'
            
        if taux >= 90:
            return 'success'
        if taux >= 60:
            return 'warning'
        return 'danger'
    
    # ===== Méthodes de classe =====
    @classmethod
    def get_evenements_du_mois(cls, annee=None, mois=None):
        """
        Récupère les événements pour un mois donné.
        
        Args:
            annee (int, optional): Année, par défaut l'année en cours
            mois (int, optional): Mois (1-12), par défaut le mois en cours
            
        Returns:
            QuerySet: Événements du mois spécifié
        """
        today = timezone.now().date()
        annee = annee or today.year
        mois = mois or today.month
        
        return cls.objects.filter(
            event_date__year=annee,
            event_date__month=mois
        ).order_by('event_date')
    
    @classmethod
    def get_stats_by_type(cls, start_date=None, end_date=None):
        """
        Statistiques de participation par type d'événement.
        
        Args:
            start_date (date, optional): Date de début pour le filtre
            end_date (date, optional): Date de fin pour le filtre
            
        Returns:
            dict: Statistiques par type d'événement
        """
        queryset = cls.objects.all()
        
        # Appliquer les filtres de date si fournis
        if start_date:
            queryset = queryset.filter(event_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_date__lte=end_date)
        
        # Agrégation par type d'événement
        stats = queryset.values('type_evenement').annotate(
            count=Count('id'),
            total_prevus=Sum('participants_prevus'),
            total_reels=Sum('participants_reels'),
            taux_moyen=Avg(
                models.Case(
                    models.When(
                        participants_prevus__gt=0,
                        then=100 * F('participants_reels') / F('participants_prevus')
                    ),
                    default=None,
                    output_field=models.FloatField()
                )
            )
        ).order_by('-count')
        
        # Conversion en dictionnaire avec libellés
        result = {}
        type_choices = dict(cls.TypeEvenement.choices)
        
        for item in stats:
            type_key = item['type_evenement']
            result[type_key] = {
                'libelle': type_choices.get(type_key, type_key),
                'nombre': item['count'],
                'participants_prevus': item['total_prevus'] or 0,
                'participants_reels': item['total_reels'] or 0,
                'taux_participation': round(item['taux_moyen'], 1) if item['taux_moyen'] else None
            }
        
        return result


================================================
FILE: rap_app/models/formations.py
================================================
import datetime
import logging
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Q, Sum, Count, Case, When, Value, ExpressionWrapper, FloatField
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


from .base import BaseModel
from .partenaires import Partenaire
from .centres import Centre
from .types_offre import TypeOffre
from .statut import Statut, get_default_color

logger = logging.getLogger("application.formation")

# ----------------------------------------------------
# Signaux déplacés dans un fichier signals/
# ----------------------------------------------------


class FormationManager(models.Manager):
    """
    Manager personnalisé pour le modèle Formation.
    Fournit des méthodes utilitaires pour filtrer et trier les formations.
    
    Utilisé dans les serializers pour:
    - Filtrer les formations selon leur état (active, à venir, terminée)
    - Trier les formations selon différents critères
    - Identifier les formations avec des places disponibles
    """

    def formations_actives(self):
        """
        Retourne uniquement les formations actives actuellement.
        
        Returns:
            QuerySet: Formations dont la date de début est passée et la date de fin est future
        """
        today = timezone.now().date()
        return self.filter(start_date__lte=today, end_date__gte=today)

    def formations_a_venir(self):
        """
        Retourne uniquement les formations qui n'ont pas encore commencé.
        
        Returns:
            QuerySet: Formations dont la date de début est dans le futur
        """
        return self.filter(start_date__gt=timezone.now().date())

    def formations_terminees(self):
        """
        Retourne uniquement les formations déjà terminées.
        
        Returns:
            QuerySet: Formations dont la date de fin est passée
        """
        return self.filter(end_date__lt=timezone.now().date())

    def formations_a_recruter(self):
        """
        Retourne les formations qui ont encore des places disponibles.
        Utilisée pour les pages de recrutement et les filtres de recherche.
        
        Returns:
            QuerySet: Formations avec des places disponibles
        """
        return self.annotate(
            total_places=models.F('prevus_crif') + models.F('prevus_mp'),
            total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp')
        ).filter(total_places__gt=models.F('total_inscrits'))

    def formations_toutes(self):
        """
        Retourne toutes les formations sans filtre.
        
        Returns:
            QuerySet: Toutes les formations
        """
        return self.all()

    def trier_par(self, champ_tri):
        """
        Trie les formations selon un champ donné, si autorisé.
        Utilisé pour les tris dans l'interface utilisateur.
        
        Args:
            champ_tri (str): Nom du champ à utiliser pour le tri, peut inclure un '-' pour tri descendant
            
        Returns:
            QuerySet: Formations triées selon le champ demandé, ou sans tri si le champ n'est pas autorisé
        """
        champs_autorises = [
            "centre", "-centre", "statut", "-statut",
            "type_offre", "-type_offre", "start_date", "-start_date",
            "end_date", "-end_date", "nom", "-nom",
            "total_places", "-total_places", "total_inscrits", "-total_inscrits",
            "taux_saturation", "-taux_saturation"
        ]
        
        if champ_tri in ["total_places", "-total_places", "total_inscrits", "-total_inscrits", 
                         "taux_saturation", "-taux_saturation"]:
            # Pour les champs calculés, nous devons annoter le queryset
            queryset = self.get_queryset().annotate(
                total_places=models.F('prevus_crif') + models.F('prevus_mp'),
                total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp'),
                taux_saturation=Case(
                    When(total_places__gt=0, 
                         then=ExpressionWrapper(
                            100.0 * models.F('total_inscrits') / models.F('total_places'),
                            output_field=FloatField()
                         )),
                    default=Value(0.0),
                    output_field=FloatField()
                )
            )
            return queryset.order_by(champ_tri)
        
        return self.get_queryset().order_by(champ_tri) if champ_tri in champs_autorises else self.get_queryset()
        
    def recherche(self, texte=None, type_offre=None, centre=None, statut=None, 
                 date_debut=None, date_fin=None, places_disponibles=False):
        """
        Recherche avancée de formations selon différents critères.
        
        Args:
            texte (str, optional): Texte à rechercher dans le nom ou les numéros
            type_offre (int, optional): ID du type d'offre
            centre (int, optional): ID du centre
            statut (int, optional): ID du statut
            date_debut (date, optional): Date de début minimum
            date_fin (date, optional): Date de fin maximum
            places_disponibles (bool, optional): Si True, seulement les formations avec places
            
        Returns:
            QuerySet: Formations correspondant aux critères
        """
        queryset = self.get_queryset()
        
        # Filtres textuels
        if texte:
            queryset = queryset.filter(
                Q(nom__icontains=texte) | 
                Q(num_kairos__icontains=texte) | 
                Q(num_offre__icontains=texte) |
                Q(num_produit__icontains=texte)
            )
        
        # Filtres sur les relations
        if type_offre:
            queryset = queryset.filter(type_offre_id=type_offre)
        if centre:
            queryset = queryset.filter(centre_id=centre)
        if statut:
            queryset = queryset.filter(statut_id=statut)
        
        # Filtres sur les dates
        if date_debut:
            queryset = queryset.filter(start_date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(end_date__lte=date_fin)
        
        # Filtre sur les places disponibles
        if places_disponibles:
            queryset = queryset.annotate(
                total_places=models.F('prevus_crif') + models.F('prevus_mp'),
                total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp')
            ).filter(total_places__gt=models.F('total_inscrits'))
        
        return queryset

    def get_formations_with_metrics(self):
        """
        Récupère les formations avec les métriques annotées pour optimiser les performances.
        
        Returns:
            QuerySet: Formations avec métriques pré-calculées
        """
        return self.annotate(
            total_places=models.F('prevus_crif') + models.F('prevus_mp'),
            total_inscrits=models.F('inscrits_crif') + models.F('inscrits_mp'),
            places_disponibles=models.ExpressionWrapper(
                models.F('total_places') - models.F('total_inscrits'),
                output_field=models.IntegerField()
            ),
            taux_saturation=Case(
                When(total_places__gt=0, 
                    then=ExpressionWrapper(
                        100.0 * models.F('total_inscrits') / models.F('total_places')