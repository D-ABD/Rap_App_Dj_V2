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
 