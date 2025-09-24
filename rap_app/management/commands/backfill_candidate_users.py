# app/management/commands/backfill_candidate_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db import transaction
from django.db.models.signals import post_save

from ...signals.candidats_signals import ensure_candidat_record

from ...models.candidat import Candidat
from ...models.custom_user import CustomUser

class Command(BaseCommand):
    help = "Lie/Crée des CustomUser pour les Candidats sans compte_utilisateur."

    def _unique_username(self, base: str) -> str:
        base = (base or "user").lower().replace(" ", "").strip(".")
        if not base:
            base = "user"
        username = base
        i = 1
        while CustomUser.objects.filter(username=username).exists():
            i += 1
            username = f"{base}{i}"
        return username

    def handle(self, *args, **options):
        # 🔌 Désactiver le signal pendant l'opération pour éviter la création auto de Candidat
        try:
            post_save.disconnect(receiver=ensure_candidat_record, sender=CustomUser)
        except Exception:
            pass

        created_count = 0
        linked_count = 0
        skipped = 0
        conflicts = 0
        errors = 0

        # Traiter *seulement* les candidats sans user
        qs = Candidat.objects.filter(compte_utilisateur__isnull=True)

        for c in qs.iterator():
            email = (c.email or "").strip().lower()
            if not email:
                skipped += 1
                self.stdout.write(f"SKIP ❌ Candidat {c.id} sans email")
                continue

            # Conflit: un AUTRE candidat a déjà un user avec ce même email
            other = (
                Candidat.objects
                .filter(compte_utilisateur__email__iexact=email)
                .exclude(pk=c.pk)
                .first()
            )
            if other:
                conflicts += 1
                self.stdout.write(
                    f"ERROR ❌ Email {email} déjà lié au candidat {other.id} (1:1 attendu)"
                )
                continue

            try:
                with transaction.atomic():
                    # Chercher un user existant (case-insensible)
                    user = CustomUser.objects.filter(email__iexact=email).first()

                    if not user:
                        base_username = (f"{(c.prenom or '').lower()}.{(c.nom or '').lower()}").strip(".") or email.split("@")[0]
                        username = self._unique_username(base_username)

                        # 🚫 Créer avec rôle neutre pour ne pas déclencher le signal
                        user = CustomUser.objects.create(
                            email=email,
                            username=username,
                            first_name=c.prenom or "",
                            last_name=c.nom or "",
                            role="test",  # rôle NON candidat ici
                            is_active=True,
                            password=make_password(get_random_string(16)),
                        )
                        created_count += 1
                        self.stdout.write(f"INFO ✅ Utilisateur créé : {email} (temp role=test)")

                    # Lier le user à ce candidat
                    c.compte_utilisateur = user
                    c.save(update_fields=["compte_utilisateur"])

                    # Puis mettre le rôle final (candidat)
                    if (user.role or "").lower() not in {"candidat", "stagiaire"}:
                        user.role = "candidat"
                        user.save(update_fields=["role"])

                    linked_count += 1
                    self.stdout.write(f"INFO 🔗 Lié candidat {c.id} ↔ user {user.id}")

            except Exception as e:
                errors += 1
                self.stdout.write(f"ERROR ❌ Erreur pour le candidat {c.id}: {str(e)}")
                continue

        # 🔌 Réactiver le signal
        try:
            post_save.connect(receiver=ensure_candidat_record, sender=CustomUser)
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS(
            f"\nBackfill terminé. Liés={linked_count}, Créés={created_count}, "
            f"Sans email ignorés={skipped}, Conflits={conflicts}, Erreurs={errors}"
        ))
        if conflicts:
            self.stdout.write(self.style.WARNING(
                "⚠️  Des emails sont déjà associés à un autre candidat. Résoudre manuellement."
            ))
