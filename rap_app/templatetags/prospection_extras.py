from django import template

register = template.Library()

PROSPECTION_STATUS_CHOICES = [
    ('a_faire', 'À faire'),
    ('en_cours', 'En cours'),
    ('a_relancer', 'À relancer'),
    ('acceptee', 'Acceptée'),
    ('refusee', 'Refusée'),
    ('annulee', 'Annulée'),
    ('non_renseigne', 'Non renseigné'),

]

@register.filter
def statut_label(value):
    dict_statuts = dict(PROSPECTION_STATUS_CHOICES)
    return dict_statuts.get(value, value)
