from django.contrib import admin
from .models import Service, SocialMediaAccount, Transaction, Order, TextToSpeechRequest, SMVaultOrder

# Register your models here.
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_k', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)
    
class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ('platform', 'link', 'is_assigned', 'created_at')
    search_fields = ('platform__name', 'link', 'logs')
    list_filter = ('platform', 'is_assigned', 'created_at')
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'quantity', 'total_price', 'provider_status', 'created_at')
    search_fields = ('service__name', 'user__email', 'provider_order_id')
    list_filter = ('provider_status', 'created_at')
    actions = ['mark_provider_resolved']

    def mark_provider_resolved(self, request, queryset):
        """Admin action to mark selected orders' provider_status as completed."""
        updated = queryset.update(provider_status='completed')
        self.message_user(request, f"Marked {updated} order(s) as provider-resolved.")
    mark_provider_resolved.short_description = 'Mark selected orders as provider-resolved'
    
class TextToSpeechRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'voice', 'status', 'created_at')
    search_fields = ('user__email',)
    list_filter = ('status', 'created_at')
    
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'reference', 'created_at')
    search_fields = ('user__email', 'reference')
    list_filter = ('transaction_type', 'created_at')

class SMVaultOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'product_name', 'quantity', 'total_price', 'status', 'provider_order_id', 'created_at')
    search_fields = ('order_id', 'user__email', 'product_name', 'provider_order_id')
    list_filter = ('status', 'created_at')
    
# class PlatformAdmin(admin.ModelAdmin):
#     list_display = ('name', 'price', 'description', 'created_at')
#     search_fields = ('name',)
#     list_filter = ('created_at',)
    
admin.site.register(Service, ServiceAdmin)
admin.site.register(SocialMediaAccount, SocialMediaAccountAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(TextToSpeechRequest, TextToSpeechRequestAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(SMVaultOrder, SMVaultOrderAdmin)
