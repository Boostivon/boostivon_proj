from django.contrib import admin
from .models import User, EmailVerification

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'email_verified', 'role', 'created_at')
    search_fields = ('email', 'username')
    list_filter = ('email_verified', 'role')

class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verified', 'created_at')
    search_fields = ('user__email', 'user__username')
    list_filter = ('verified','created_at')

admin.site.register(User, UserAdmin)
admin.site.register(EmailVerification, EmailVerificationAdmin)