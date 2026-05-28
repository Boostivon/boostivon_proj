from django.contrib import admin
from .models import Service, SocialMediaAccount, Transaction, Order, TextToSpeechRequest

# Register your models here.
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_k', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    
class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ('platform', 'username', 'created_at')
    search_fields = ('platform', 'username')
    list_filter = ('platform', 'created_at')
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'quantity', 'total_price', 'created_at')
    search_fields = ('service__name', 'user__email')
    list_filter = ('created_at',)
    
class TextToSpeechRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'voice', 'status', 'created_at')
    search_fields = ('user__email',)
    list_filter = ('status', 'created_at')
    
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'reference', 'created_at')
    search_fields = ('user__email', 'reference')
    list_filter = ('transaction_type', 'created_at')
    
# class PlatformAdmin(admin.ModelAdmin):
#     list_display = ('name', 'price', 'description', 'created_at')
#     search_fields = ('name',)
#     list_filter = ('created_at',)
    
admin.site.register(Service, ServiceAdmin)
admin.site.register(SocialMediaAccount, SocialMediaAccountAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(TextToSpeechRequest, TextToSpeechRequestAdmin)
admin.site.register(Transaction, TransactionAdmin)