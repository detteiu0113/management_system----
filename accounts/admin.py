from django.contrib import admin
from .models import CustomUser, OwnerProfile, ParentProfile, TeacherProfile, TeachingPermission

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_superuser', 'is_owner', 'is_parent', 'is_teacher']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(OwnerProfile)
admin.site.register(ParentProfile)
admin.site.register(TeacherProfile)
admin.site.register(TeachingPermission)