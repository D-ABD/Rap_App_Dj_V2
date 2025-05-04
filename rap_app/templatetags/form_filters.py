from django import template
from ..models.prepacomp import PrepaCompGlobal

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """Ajoute une classe CSS à un champ de formulaire"""
    return field.as_widget(attrs={"class": css_class})

@register.simple_tag
def get_mois_stats(centre, annee):
    """Récupère les statistiques mensuelles"""
    return PrepaCompGlobal.stats_par_mois(annee, centre)

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    return dictionary.get(key)

@register.filter
def sum_ateliers(ateliers):
    """Calcule la somme des totaux des ateliers"""
    return sum(atelier['total'] for atelier in ateliers)

@register.filter
def widthratio_filter(value, max_value, scale=100):
    """Version filtre de la tag widthratio"""
    try:
        return int(float(value) / float(max_value) * float(scale))
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplie la valeur par l'argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divise la valeur par l'argument"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0    

@register.filter
def startswith(text, starts):
    """Vérifie si une chaîne commence par un préfixe donné"""
    if isinstance(text, str):
        return text.startswith(starts)
    return False