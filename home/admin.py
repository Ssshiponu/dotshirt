from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'message_preview']
    search_fields = ['name', 'email', 'message']
    
    def message_preview(self, obj):
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message
    
    message_preview.short_description = 'Message'
