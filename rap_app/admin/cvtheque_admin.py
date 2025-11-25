from django.contrib import admin
from django.utils.html import format_html

from ..models.cvtheque import CVTheque


@admin.register(CVTheque)
class CVThequeAdmin(admin.ModelAdmin):

    # ----------------------------
    # 📌 Colonnes affichées en liste
    # ----------------------------
    list_display = (
        "id",
        "titre",
        "document_type",
        "candidat_fullname",
        "formation_nom",
        "formation_centre",
        "est_public",
        "date_depot",
        "preview_link",
    )

    # ----------------------------
    # 📌 Filtres
    # ----------------------------
    list_filter = (
        "document_type",
        "est_public",
        "candidat__formation__centre",
        "candidat__formation__type_offre",
        "candidat__formation__statut",
        "date_depot",
    )

    # ----------------------------
    # 📌 Lecture seule
    # ----------------------------
    readonly_fields = (
        "date_depot",
        "extension",
        "taille",
        "preview_file",

        # 👉 propriétés du modèle (elles existent !)
        "formation_nom",
        "formation_centre",
        "formation_type_offre",
        "formation_statut",
        "formation_start_date",
        "formation_end_date",
        "formation_resume",
        "candidat_ville",
        "candidat_type_contrat_display",
        "candidat_cv_statut_display",
    )

    # ----------------------------
    # 📌 Recherche
    # ----------------------------
    search_fields = (
        "titre",
        "mots_cles",
        "candidat__nom",
        "candidat__prenom",
        "candidat__email",
        "candidat__ville",
    )

    list_select_related = (
        "candidat",
        "candidat__formation",
        "candidat__formation__centre",
        "candidat__formation__type_offre",
        "candidat__formation__statut",
    )

    # ----------------------------
    # 📌 Formulaire admin
    # ----------------------------
    fieldsets = (
        ("📄 Document", {
            "fields": (
                "titre",
                "document_type",
                "fichier",
                "preview_file",
                "mots_cles",
                "est_public",
                "date_depot",
                "extension",
                "taille",
            )
        }),
        ("👤 Candidat", {
            "fields": (
                "candidat",
                "candidat_ville",
                "candidat_type_contrat_display",
                "candidat_cv_statut_display",
            )
        }),
        ("🎓 Formation associée", {
            "fields": (
                "formation_nom",
                "formation_type_offre",
                "formation_centre",
                "formation_statut",
                "formation_start_date",
                "formation_end_date",
                "formation_resume",
            )
        }),
        ("🔐 Consentements", {
            "fields": (
                "consentement_stockage_cv",
                "consentement_transmission_cv",
                "date_consentement_cv",
            )
        }),
    )

    # ----------------------------
    # 📌 Actions admin
    # ----------------------------
    actions = ["marquer_public", "marquer_prive"]

    @admin.action(description="Rendre public les documents sélectionnés")
    def marquer_public(self, request, queryset):
        count = queryset.update(est_public=True)
        self.message_user(request, f"{count} documents rendus publics.")

    @admin.action(description="Rendre privé les documents sélectionnés")
    def marquer_prive(self, request, queryset):
        count = queryset.update(est_public=False)
        self.message_user(request, f"{count} documents rendus privés.")

    # ----------------------------
    # 📌 Colonnes
    # ----------------------------
    def candidat_fullname(self, obj):
        return f"{obj.candidat.prenom} {obj.candidat.nom}"
    candidat_fullname.short_description = "Candidat"

    def preview_link(self, obj):
        if not obj.fichier:
            return "-"
        return format_html(
            "<a href='{}' target='_blank'><strong>Ouvrir</strong></a>",
            obj.fichier.url
        )

    # ----------------------------
    # 📌 Aperçu PDF intégré
    # ----------------------------
    def preview_file(self, obj):
        if not obj.fichier:
            return "Aucun fichier"
        url = obj.fichier.url

        if obj.extension.lower() == "pdf":
            return format_html(
                """
                <embed src="{}" type="application/pdf"
                       width="100%" height="600px" style="border:1px solid #ccc;" />
                """,
                url
            )

        return format_html("<a href='{}' target='_blank'>Télécharger</a>", url)

    preview_file.short_description = "Aperçu du fichier"
