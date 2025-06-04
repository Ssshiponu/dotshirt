from django.contrib import admin
from .models import Order, OrderItem, OrderTracker, Address

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'size', 'color', 'quantity', 'price']
    readonly_fields = ['price']
    raw_id_fields = ['product']

class OrderTrackerInline(admin.TabularInline):
    model = OrderTracker
    extra = 0
    fields = ['status', 'description', 'timestamp', 'location']
    readonly_fields = ['timestamp']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'total_price', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'shipping_address__full_name', 'shipping_address__phone']
    readonly_fields = ['order_number', 'created_at']
    inlines = [OrderItemInline, OrderTrackerInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'created_at')
        }),
        ('Customer', {
            'fields': ('user', 'session_id', 'shipping_address')
        }),
        ('Payment', {
            'fields': ('payment_method', 'delivery_charge', 'total_price')
        }),
    )
    
    def full_name(self, obj):
        return obj.shipping_address.full_name if obj.shipping_address else ''
    
    def phone(self, obj):
        return obj.shipping_address.phone if obj.shipping_address else ''
    
    full_name.short_description = 'Customer Name'
    phone.short_description = 'Phone'

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'short_address', 'user']
    list_filter = ['user']
    search_fields = ['full_name', 'phone', 'email', 'full_address']
    
    def short_address(self, obj):
        if len(obj.full_address) > 50:
            return f"{obj.full_address[:50]}..."
        return obj.full_address
    
    short_address.short_description = 'Address'
