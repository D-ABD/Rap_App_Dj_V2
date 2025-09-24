# rap_app/signals/candidats_signals.py
from django.db import transaction, IntegrityError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
import logging

from ..models.candidat import Candidat
from ..models.custom_user import CustomUser
from ..models.prospection import Prospection

logger = logging.getLogger(__name__)

# inclut bien "candidatuser"
CANDIDATE_ROLES = {
    getattr(CustomUser, "ROLE_CANDIDAT", "candidat"),
    getattr(CustomUser, "ROLE_STAGIAIRE", "stagiaire"),
    getattr(CustomUser, "ROLE_CANDIDAT_USER", "candidatuser"),
}


# --------------------------- helpers ---------------------------
def _nn(val: str | None) -> str:
    """Normalize nullable char to non-null trimmed string (may be '')."""
    return (val or "").strip()


def _email_local(email: str | None) -> str:
    e = _nn(email).lower()
    return e.split("@", 1)[0] if "@" in e else e


def _safe_non_blank(primary: str | None, *fallbacks: str, default: str = "Inconnu") -> str:
    """
    Retourne la 1ère valeur non vide parmi primary puis fallbacks, sinon `default`.
    Utile pour remplir Candidat.nom/prenom (blank=False) même si user n'a rien.
    """
    for v in (primary, *fallbacks):
        v = _nn(v)
        if v:
            return v
    return default


# ─────────────────────────────────────────────────────────
# A. CustomUser -> Candidat (changement de rôle / post_save)
# ─────────────────────────────────────────────────────────
@receiver(pre_save, sender=CustomUser)
def _remember_old_role(sender, instance: CustomUser, **kwargs):
    """Mémorise l'ancien rôle pour détecter une bascule éventuelle."""
    if not instance.pk:
        instance._old_role = None  # type: ignore[attr-defined]
    else:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_role = old.role  # type: ignore[attr-defined]
        except sender.DoesNotExist:
            instance._old_role = None  # type: ignore[attr-defined]


@receiver(post_save, sender=CustomUser)
def ensure_candidat_record(sender, instance: CustomUser, created: bool, **kwargs):
    """
    Si le user a un rôle 'candidat-like' :
      1) si un Candidat est déjà lié -> OK
      2) sinon réconcilier par email (candidat sans compte)
      3) sinon créer un Candidat minimal lié au user (nom/prenom non vides)
    """
    role = (_nn(instance.role)).lower()
    if role not in CANDIDATE_ROLES:
        return

    # (1) déjà lié ?
    if Candidat.objects.filter(compte_utilisateur=instance).exists():
        return

    email = _nn(instance.email).lower()
    local = _email_local(email)
    safe_nom = _safe_non_blank(instance.last_name, instance.username, local)
    safe_prenom = _safe_non_blank(instance.first_name)

    if email:
        # (2) réconcilier par email d'abord
        try:
            with transaction.atomic():
                cand = (
                    Candidat.objects
                    .select_for_update(skip_locked=True)
                    .filter(compte_utilisateur__isnull=True, email__iexact=email)
                    .order_by("id")
                    .first()
                )
                if cand:
                    # garantir nom/prenom non vides (blank=False)
                    if not _nn(cand.nom):
                        cand.nom = safe_nom
                    if not _nn(cand.prenom):
                        cand.prenom = safe_prenom
                    cand.compte_utilisateur = instance
                    cand.save(update_fields=["compte_utilisateur", "nom", "prenom"])
                    logger.info("🔗 Réconciliation Candidat #%s ↔ User #%s (email=%s)", cand.pk, instance.pk, email)
                    return
        except IntegrityError as e:
            logger.warning("⚠️ Conflit réconciliation CustomUser->Candidat (email=%s): %s", email, e)

    # (3) créer si rien de réconciliable — ⚠️ nom/prenom non vides
    Candidat.objects.get_or_create(
        compte_utilisateur=instance,
        defaults={
            "nom": safe_nom,
            "prenom": safe_prenom,
            "email": email or None,
        },
    )
    logger.info("➕ Candidat créé (ou récupéré) pour User #%s (role=%s)", instance.pk, role)


# ─────────────────────────────────────────────────────────
# Abis. CustomUser role change → unlink Candidat si besoin
# ─────────────────────────────────────────────────────────
@receiver(post_save, sender=CustomUser)
def unlink_candidat_if_role_not_candidate(sender, instance: CustomUser, **kwargs):
    """
    Si le rôle de l'utilisateur sort du périmètre 'candidat',
    on casse le lien avec le modèle Candidat.
    """
    role = (_nn(instance.role)).lower()
    if role in CANDIDATE_ROLES:
        return  # il reste candidat-like → pas de changement

    cand = getattr(instance, "candidat_associe", None)
    if not cand:
        return

    cand.compte_utilisateur = None
    cand.save(update_fields=["compte_utilisateur"])
    logger.info(
        "🚫 Lien Candidat #%s ↔ User #%s supprimé (role=%s)",
        cand.pk, instance.pk, role
    )


# ─────────────────────────────────────────────────────────
# B. Candidat -> CustomUser (filet de sécurité / post_save)
# ─────────────────────────────────────────────────────────
def _build_unique_username(base: str) -> str:
    base = _nn(base).lower().replace(" ", "").strip(".") or "user"
    username = base
    i = 1
    while CustomUser.objects.filter(username=username).exists():
        i += 1
        username = f"{base}{i}"
    return username


@receiver(post_save, sender=Candidat)
def ensure_user_for_candidate(sender, instance: Candidat, created: bool, **kwargs):
    """
    Si un Candidat n'a pas de compte_utilisateur mais a un email :
      - lier à un CustomUser existant (même email) si non déjà lié à un autre candidat
      - sinon créer un CustomUser neutre (role=test), lier, puis passer le rôle à 'candidat'
    """
    if instance.compte_utilisateur_id:
        return

    email = _nn(instance.email).lower()
    if not email:
        return

    user = CustomUser.objects.filter(email__iexact=email).first()
    if user:
        # Évite un conflit 1:1 (un user pour plusieurs candidats)
        if Candidat.objects.filter(compte_utilisateur=user).exclude(pk=instance.pk).exists():
            logger.warning("⚠️ User #%s (email=%s) déjà lié à un autre Candidat. Skip.", user.pk, email)
            return

        # Lier sans retrigger inutilement le signal post_save(Candidat)
        type(instance).objects.filter(pk=instance.pk).update(compte_utilisateur=user)
        logger.info("🔗 Lien Candidat #%s ↔ User #%s (email=%s)", instance.pk, user.pk, email)

        # S'assurer du rôle final côté user
        if (_nn(user.role)).lower() not in CANDIDATE_ROLES:
            user.role = getattr(CustomUser, "ROLE_CANDIDAT", "candidat")
            user.save(update_fields=["role"])
        return

    # Aucun user existant : en créer un NEUTRE pour éviter une création auto de Candidat
    base_username = _nn(f"{_nn(instance.prenom).lower()}.{_nn(instance.nom).lower()}") or email.split("@")[0]
    username = _build_unique_username(base_username)

    try:
        with transaction.atomic():
            # 1) créer le user avec rôle "test" (ne déclenche pas ensure_candidat_record)
            new_user = CustomUser.objects.create(
                email=email,
                username=username,
                first_name=_nn(instance.prenom),
                last_name=_nn(instance.nom),
                role=getattr(CustomUser, "ROLE_TEST", "test"),  # rôle neutre
                is_active=True,
                password=make_password(get_random_string(16)),
            )
            logger.info("✅ User créé #%s (email=%s, role=test)", new_user.pk, email)

            # 2) lier ce user au candidat SANS retrigger post_save(Candidat)
            type(instance).objects.filter(pk=instance.pk).update(compte_utilisateur=new_user)
            logger.info("🔗 Lien Candidat #%s ↔ User #%s", instance.pk, new_user.pk)

            # 3) passer le user au rôle final (déclenchera ensure_candidat_record mais idempotent)
            new_user.role = getattr(CustomUser, "ROLE_CANDIDAT", "candidat")
            new_user.save(update_fields=["role"])
            logger.info("🛠️ User #%s rôle mis à 'candidat'", new_user.pk)

    except IntegrityError as e:
        logger.error("❌ IntegrityError ensure_user_for_candidate (cand#%s, email=%s): %s", instance.pk, email, e)


# ─────────────────────────────────────────────────────────
# C. Prospection : caler formation depuis l’owner (create / owner changé)
# ─────────────────────────────────────────────────────────
@receiver(pre_save, sender=Prospection)
def sync_formation_from_owner(sender, instance: Prospection, **kwargs):
    """
    Si un owner est défini et possède une formation via son Candidat :
      - à la création : toujours caler la formation
      - en update : recaler si l'owner change OU si la formation est vide
    """
    owner = getattr(instance, "owner", None)
    if not owner:
        return

    cand = getattr(owner, "candidat_associe", None) or getattr(owner, "candidat", None)
    f_id = getattr(cand, "formation_id", None)
    if not f_id:
        return

    if instance._state.adding:
        instance.formation_id = f_id
        return

    try:
        old = Prospection.objects.only("owner_id", "formation_id").get(pk=instance.pk)
    except Prospection.DoesNotExist:
        instance.formation_id = f_id
        return

    owner_changed = old.owner_id != getattr(instance, "owner_id", None)
    no_formation = not getattr(instance, "formation_id", None)

    if owner_changed or no_formation:
        instance.formation_id = f_id
