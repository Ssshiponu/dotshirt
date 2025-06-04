from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ['phone']

class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'is_staff']
    list_filter = ['is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__phone']
    
    def phone_number(self, obj):
        if hasattr(obj, 'profile') and obj.profile and obj.profile.phone:
            return obj.profile.phone
        return ''
    
    phone_number.short_description = 'Phone'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)