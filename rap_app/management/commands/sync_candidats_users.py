# rap_app/management/commands/sync_candidats_users.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
import logging

from rap_app.models.candidat import Candidat
from rap_app.models.custom_user import CustomUser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Associer un compte utilisateur à chaque candidat sans compte_utilisateur"

    def handle(self, *args, **options):
        candidats = Candidat.objects.filter(compte_utilisateur__isnull=True)
        total = candidats.count()
        created, linked, skipped = 0, 0, 0

        self.stdout.write(f"🔎 {total} candidats sans compte trouvé(s).")

        for c in candidats:
            email = (c.email or "").strip().lower()

            # 1. Si pas d’email → générer un email factice
            if not email:
                base = f"{(c.prenom or 'inconnu').lower()}.{(c.nom or 'inconnu').lower()}.{c.pk}"
                email = f"{base}@fake.local"
                self.stdout.write(
                    self.style.WARNING(f"⚠️ Candidat #{c.pk} sans email → génération {email}")
                )

            # 2. Essayer de réconcilier par email
            user = CustomUser.objects.filter(email__iexact=email).first()
            if user:
                # Vérifier si déjà lié à un autre candidat
                if Candidat.objects.filter(compte_utilisateur=user).exclude(pk=c.pk).exists():
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ User #{user.pk} ({user.email}) déjà lié à un autre candidat → skip pour Candidat #{c.pk}"
                        )
                    )
                    continue

                Candidat.objects.filter(pk=c.pk).update(compte_utilisateur=user, email=email)
                linked += 1
                self.stdout.write(f"🔗 Lié Candidat #{c.pk} ↔ User #{user.pk} ({user.email})")
                continue

            # 3. Créer un nouvel utilisateur (rôle neutre pour éviter les signaux)
            base_username = f"{(c.prenom or 'inconnu').lower()}.{(c.nom or 'inconnu').lower()}".replace(" ", "")
            if not base_username:
                base_username = f"user{c.pk}"
            username = base_username
            i = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{i}"
                i += 1

            with transaction.atomic():
                # Étape A : créer user avec rôle neutre
                user = CustomUser.objects.create(
                    email=email,
                    username=username,
                    first_name=c.prenom or "",
                    last_name=c.nom or "",
                    role=getattr(CustomUser, "ROLE_TEST", "test"),  # rôle temporaire
                    is_active=True,
                    password=make_password(get_random_string(16)),
                )
                # Étape B : lier directement via update() (pas de full_clean())
                Candidat.objects.filter(pk=c.pk).update(compte_utilisateur=user, email=email)
                # Étape C : mettre le rôle final
                user.role = getattr(CustomUser, "ROLE_CANDIDAT", "candidat")
                user.save(update_fields=["role"])

                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ User #{user.pk} créé et lié à Candidat #{c.pk}")
                )

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Terminé : {created} users créés, {linked} liés, {skipped} ignorés, total traité = {total}"
        ))
