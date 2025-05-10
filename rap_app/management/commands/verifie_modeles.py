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