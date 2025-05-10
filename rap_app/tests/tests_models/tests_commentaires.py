from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import timedelta

from ...models.centres import Centre
from ...models.statut import Statut
from ...models.types_offre import TypeOffre

from ...models import Commentaire, Formation
from .setup_base_tests import BaseModelTestSetupMixin


class CommentaireModelTest(BaseModelTestSetupMixin):
    def setUp(self):
        super().setUp()

        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.NON_DEFINI)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)

        self.formation = self.create_instance(
            Formation,
            nom="Formation Test",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut
        )

        self.commentaire = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Un commentaire de test."
        )


    def test_str_and_repr(self):
        commentaire = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Contenu de test",
            created_by=self.user
        )
        self.assertIn("Commentaire de", str(commentaire))
        self.assertIn("formation=", repr(commentaire))

    def test_clean_validation_saturation(self):
        with self.assertRaises(ValidationError):
            commentaire = Commentaire(formation=self.formation, contenu="Test", saturation=150)
            commentaire.full_clean()

    def test_clean_validation_empty_contenu(self):
        with self.assertRaises(ValidationError):
            commentaire = Commentaire(formation=self.formation, contenu="   ")
            commentaire.full_clean()

    def test_save_strip_tags_and_limit_saturation(self):
        commentaire = Commentaire.objects.create(
            formation=self.formation,
            contenu="<b>Hello</b>",
            saturation=999,
            created_by=self.user
        )
        self.assertEqual(commentaire.contenu, "Hello")
        self.assertLessEqual(commentaire.saturation, 100)

    def test_delete_commentaire_updates_formation(self):
        commentaire = Commentaire.objects.create(
            formation=self.formation,
            contenu="À supprimer",
            saturation=80,
            created_by=self.user
        )
        commentaire_id = commentaire.pk
        commentaire.delete()
        self.assertFalse(Commentaire.objects.filter(pk=commentaire_id).exists())

    def test_auteur_nom(self):
        commentaire = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Test",
            created_by=self.user
        )
        self.assertEqual(commentaire.auteur_nom, self.user.username)

    def test_get_content_preview(self):
        commentaire = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Texte court",
            created_by=self.user
        )
        self.assertIn("Texte", commentaire.get_content_preview(10))

    def test_is_recent_true(self):
        commentaire = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Récence",
            created_by=self.user
        )
        self.assertTrue(commentaire.is_recent())

    def test_is_edited_false(self):
        commentaire = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Pas modifié",
            created_by=self.user
        )
        self.assertFalse(commentaire.is_edited())

    def test_to_serializable_dict(self):
        commentaire = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Contenu complet",
            created_by=self.user
        )
        data = commentaire.to_serializable_dict()
        self.assertIn("formation_id", data)
        self.assertIn("contenu", data)
        self.assertIn("auteur", data)

    def test_get_all_commentaires(self):
        c1 = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="ABC",
            created_by=self.user
        )
        results = Commentaire.get_all_commentaires(formation_id=self.formation.id)
        self.assertIn(c1, results)

    def test_get_recent_commentaires(self):
        c1 = self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="Récemment",
            created_by=self.user
        )
        results = Commentaire.get_recent_commentaires(limit=1)
        self.assertEqual(len(results), 1)

    def test_get_saturation_stats(self):
        self.create_instance(
            Commentaire,
            formation=self.formation,
            contenu="S1",
            created_by=self.user,
            saturation=50
        )
        stats = Commentaire.get_saturation_stats(formation_id=self.formation.id)
        self.assertIn("avg", stats)
        self.assertEqual(stats["count"], 1)
