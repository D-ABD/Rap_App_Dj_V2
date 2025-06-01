from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime


class BaseAdminMixin(admin.ModelAdmin):
    """
    🔧 Admin générique pour tous les modèles héritant de BaseModel.
    Fournit des champs en lecture seule, des filtres et des actions standards.
    """

    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    list_filter = ('is_active', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['activer', 'desactiver']
    list_display_links = ('id',)

    # Champs optionnels à surcharger si besoin dans l'admin enfant
    search_fields = ()
    
    def created_at_display(self, obj):
        if obj.created_at:
            return localtime(obj.created_at).strftime('%Y-%m-%d %H:%M:%S')
        return "—"
    created_at_display.short_description = 'Créé le'

    def updated_at_display(self, obj):
        if obj.updated_at:
            return localtime(obj.updated_at).strftime('%Y-%m-%d %H:%M:%S')
        return "—"
    updated_at_display.short_description = 'Modifié le'

    def created_by_display(self, obj):
        return str(obj.created_by) if obj.created_by else "—"
    created_by_display.short_description = 'Créé par'

    def updated_by_display(self, obj):
        return str(obj.updated_by) if obj.updated_by else "—"
    updated_by_display.short_description = 'Modifié par'

    @admin.action(description="🔒 Désactiver les objets sélectionnés")
    def desactiver(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} objet(s) désactivé(s).")

    @admin.action(description="✅ Réactiver les objets sélectionnés")
    def activer(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} objet(s) réactivé(s).")
