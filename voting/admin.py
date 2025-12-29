from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, Batch, Candidate, Vote

# 1. Custom User Admin (To handle the new fields like 'role' and 'face_encoding')
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ('College Info', {'fields': ('role', 'batch')}),
        ('Voting Status', {'fields': ('has_voted_phase1', 'has_voted_phase2', 'is_password_changed')}),
    )
    list_display = ['username', 'email', 'role', 'batch', 'is_password_changed']
    list_filter = ['role', 'batch', 'is_password_changed']

# 2. Register all models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Batch)
admin.site.register(Candidate)
admin.site.register(Vote)