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