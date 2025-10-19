# rap_app/signals/candidats_signals.py
import logging
from django.db import transaction, IntegrityError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string

from ..models.candidat import Candidat
from ..models.custom_user import CustomUser
from ..models.prospection import Prospection

logger = logging.getLogger(__name__)

# Rôles considérés comme "candidats"
CANDIDATE_ROLES = {
    getattr(CustomUser, "ROLE_CANDIDAT", "candidat"),
    getattr(CustomUser, "ROLE_STAGIAIRE", "stagiaire"),
    getattr(CustomUser, "ROLE_CANDIDAT_USER", "candidatuser"),
}

# --------------------------- helpers ---------------------------
def _nn(val: str | None) -> str:
    return (val or "").strip()

def _email_local(email: str | None) -> str:
    e = _nn(email).lower()
    return e.split("@", 1)[0] if "@" in e else e

def _safe_non_blank(primary: str | None, *fallbacks: str, default: str = "Inconnu") -> str:
    for v in (primary, *fallbacks):
        v = _nn(v)
        if v:
            return v
    return default

def _build_unique_username(base: str) -> str:
    base = _nn(base).lower().replace(" ", "").strip(".") or "user"
    username = base
    i = 1
    while CustomUser.objects.filter(username=username).exists():
        i += 1
        username = f"{base}{i}"
    return username

# ──────────────────────────────────────────────────────────────
# A. Gestion User <-> Candidat
# ──────────────────────────────────────────────────────────────
@receiver(pre_save, sender=CustomUser)
def _remember_old_role(sender, instance: CustomUser, **kwargs):
    """Mémorise l'ancien rôle avant update pour détecter une bascule."""
    if not instance.pk:
        instance._old_role = None  # type: ignore[attr-defined]
    else:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_role = old.role  # type: ignore[attr-defined]
        except sender.DoesNotExist:
            instance._old_role = None  # type: ignore[attr-defined]

@receiver(post_save, sender=CustomUser)
def sync_candidat_for_user(sender, instance: CustomUser, created: bool, **kwargs):
    """
    Garantit la cohérence entre User et Candidat :
    - Si le rôle est "candidat-like":
        * si déjà lié → OK
        * sinon réconcilier par email
        * sinon créer un candidat minimal
    - Si le rôle sort du périmètre "candidat-like":
        * casser le lien avec Candidat (compte_utilisateur=None)
    """
    role = (_nn(instance.role)).lower()

    # Cas 1 : rôle candidat-like
    if role in CANDIDATE_ROLES:
        if Candidat.objects.filter(compte_utilisateur=instance).exists():
            return

        email = _nn(instance.email).lower()
        local = _email_local(email)
        safe_nom = _safe_non_blank(instance.last_name, instance.username, local)
        safe_prenom = _safe_non_blank(instance.first_name)

        if email:
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
                        if not _nn(cand.nom):
                            cand.nom = safe_nom
                        if not _nn(cand.prenom):
                            cand.prenom = safe_prenom
                        cand.compte_utilisateur = instance
                        cand.save(update_fields=["compte_utilisateur", "nom", "prenom"])
                        logger.info("🔗 Réconciliation Candidat #%s ↔ User #%s", cand.pk, instance.pk)
                        return
            except IntegrityError as e:
                logger.warning("⚠️ Conflit réconciliation User->Candidat (email=%s): %s", email, e)

        # Si pas trouvé : créer un candidat minimal
        Candidat.objects.get_or_create(
            compte_utilisateur=instance,
            defaults={"nom": safe_nom, "prenom": safe_prenom, "email": email or None},
        )
        logger.info("➕ Candidat créé pour User #%s (role=%s)", instance.pk, role)
        return

    # Cas 2 : rôle non candidat → délier
    cand = getattr(instance, "candidat_associe", None)
    if cand:
        cand.compte_utilisateur = None
        cand.save(update_fields=["compte_utilisateur"])
        logger.info("🚫 Lien Candidat #%s ↔ User #%s supprimé (role=%s)", cand.pk, instance.pk, role)


@receiver(post_save, sender=Candidat)
def ensure_user_for_candidate(sender, instance: Candidat, created: bool, **kwargs):
    """
    Garantit qu'un Candidat a un User associé si email disponible :
    - si un user existe avec le même email → lier
    - sinon créer un user ROLE_TEST puis basculer en ROLE_CANDIDAT
    """
    if instance.compte_utilisateur_id:
        return

    email = _nn(instance.email).lower()
    if not email:
        return

    user = CustomUser.objects.filter(email__iexact=email).first()
    if user:
        if Candidat.objects.filter(compte_utilisateur=user).exclude(pk=instance.pk).exists():
            logger.warning("⚠️ User #%s déjà lié à un autre Candidat. Skip.", user.pk)
            return
        type(instance).objects.filter(pk=instance.pk).update(compte_utilisateur=user)
        logger.info("🔗 Lien Candidat #%s ↔ User #%s", instance.pk, user.pk)

        if (_nn(user.role)).lower() not in CANDIDATE_ROLES:
            user.role = getattr(CustomUser, "ROLE_CANDIDAT", "candidat")
            user.save(update_fields=["role"])
        return

    username = _build_unique_username(f"{instance.prenom}.{instance.nom}" or email.split("@")[0])
    try:
        with transaction.atomic():
            new_user = CustomUser.objects.create(
                email=email,
                username=username,
                first_name=_nn(instance.prenom),
                last_name=_nn(instance.nom),
                role=getattr(CustomUser, "ROLE_TEST", "test"),
                is_active=True,
                password=make_password(get_random_string(16)),
            )
            type(instance).objects.filter(pk=instance.pk).update(compte_utilisateur=new_user)
            logger.info("✅ User créé #%s puis lié à Candidat #%s", new_user.pk, instance.pk)

            new_user.role = getattr(CustomUser, "ROLE_CANDIDAT", "candidat")
            new_user.save(update_fields=["role"])
    except IntegrityError as e:
        logger.error("❌ IntegrityError ensure_user_for_candidate (cand#%s, email=%s): %s", instance.pk, email, e)

# ──────────────────────────────────────────────────────────────
# C. Prospection -> formation héritée du candidat
# ──────────────────────────────────────────────────────────────
@receiver(pre_save, sender=Prospection)
def sync_formation_from_owner(sender, instance: Prospection, **kwargs):
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

    if old.owner_id != getattr(instance, "owner_id", None) or not getattr(instance, "formation_id", None):
        instance.formation_id = f_id
