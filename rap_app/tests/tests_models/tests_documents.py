from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from rap_app.models import Document, Formation, TypeOffre, Centre, Statut
from .setup_base_tests import BaseModelTestSetupMixin


class DocumentModelTest(BaseModelTestSetupMixin):
    """🧪 Tests unitaires du modèle Document."""

    def setUp(self):
        super().setUp()

        # Dépendances pour la formation
        self.centre = self.create_instance(Centre, nom="Centre Test")
        self.type_offre = self.create_instance(TypeOffre, nom=TypeOffre.CRIF)
        self.statut = self.create_instance(Statut, nom=Statut.NON_DEFINI)

        # Formation liée
        self.formation = self.create_instance(
            Formation,
            nom="Formation pour document",
            centre=self.centre,
            type_offre=self.type_offre,
            statut=self.statut,
        )

        # Fichier PDF valide
        self.valid_file = SimpleUploadedFile(
            "test.pdf", b"%PDF-1.4 test content", content_type="application/pdf"
        )

    def test_create_valid_pdf_document(self):
        doc = Document(
            formation=self.formation,
            nom_fichier="Document Test",
            fichier=self.valid_file,
            type_document=Document.PDF,
            created_by=self.user,
            updated_by=self.user,
        )
        doc.full_clean()  # Ne lève pas d'erreur
        doc.save(skip_history=True)  # on évite d'enregistrer dans HistoriqueFormation ici
        self.assertEqual(doc.extension, "pdf")
        self.assertTrue("pdf" in doc.mime_type or doc.mime_type == "application/pdf")

    def test_invalid_extension_raises_error(self):
        fake_file = SimpleUploadedFile("bad.exe", b"fake content", content_type="application/octet-stream")
        doc = Document(
            formation=self.formation,
            nom_fichier="Fichier interdit",
            fichier=fake_file,
            type_document=Document.PDF,
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(ValidationError):
            doc.full_clean()

    def test_large_file_raises_validation(self):
        large_file = SimpleUploadedFile("big.pdf", b"a" * (11 * 1024 * 1024), content_type="application/pdf")
        doc = Document(
            formation=self.formation,
            nom_fichier="Gros fichier",
            fichier=large_file,
            type_document=Document.PDF,
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(ValidationError):
            doc.full_clean()

    def test_str_representation(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="Un document vraiment très long pour voir si la coupe fonctionne correctement dans str",
            fichier=self.valid_file,
            type_document=Document.PDF
        )
        self.assertIn("Un document vraiment", str(doc))

    def test_serializable_dict_contains_expected_keys(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="Fichier Exportable",
            fichier=self.valid_file,
            type_document=Document.PDF
        )
        data = doc.to_serializable_dict()
        expected_keys = [
            "id", "nom_fichier", "type_document", "taille_fichier", "extension",
            "mime_type", "download_url", "icon_class", "created_at", "created_by"
        ]
        for key in expected_keys:
            self.assertIn(key, data)

    def test_delete_creates_historique_entry(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="Suppression test",
            fichier=self.valid_file,
            type_document=Document.PDF
        )
        doc.delete(skip_history=False, user=self.user)
        self.assertTrue(
            self.formation.historiques.filter(
                commentaire__icontains="Suppression"
            ).exists()
        )


    def test_clean_rejects_empty_nom_fichier(self):
        doc = Document(
            formation=self.formation,
            nom_fichier="  ",
            fichier=self.valid_file,
            type_document=Document.PDF
        )
        with self.assertRaises(ValidationError):
            doc.full_clean()

    def test_icon_class_returns_correct_value(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="icon test",
            fichier=self.valid_file,
            type_document=Document.PDF
        )
        self.assertEqual(doc.icon_class, "fa-file-pdf")



    def test_is_viewable_in_browser_for_pdf(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="affichable",
            fichier=self.valid_file,
            type_document=Document.PDF,
            mime_type="application/pdf"
        )
        self.assertTrue(doc.is_viewable_in_browser)

    def test_get_download_url_returns_url(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="Téléchargement",
            fichier=self.valid_file,
            type_document=Document.PDF
        )
        # Simule un nom de fichier stocké pour obtenir un chemin plausible
        doc.fichier.name = "formations/documents/pdf/1/test.pdf"
        self.assertTrue(doc.get_download_url().endswith("/test.pdf"))


    def test_human_size_for_small_file(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="small",
            fichier=self.valid_file,
            type_document=Document.PDF,
        )
        doc.taille_fichier = 512  # Ajout après instanciation
        self.assertEqual(doc.human_size, "512 Ko")

    def test_human_size_for_large_file(self):
        doc = self.create_instance(
            Document,
            formation=self.formation,
            nom_fichier="big",
            fichier=self.valid_file,
            type_document=Document.PDF,
        )
        doc.taille_fichier = 2048
        self.assertEqual(doc.human_size, "2.0 Mo")


    def test_save_creates_historique_entry(self):
        doc = Document(
            formation=self.formation,
            nom_fichier="Ajout historique",
            fichier=self.valid_file,
            type_document=Document.PDF,
            created_by=self.user,
            updated_by=self.user
        )
        doc.save(skip_history=False)
        self.assertTrue(
            self.formation.historiques.filter(
                commentaire__icontains="Ajout du document"
            ).exists()
        )
