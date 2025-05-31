from django.contrib import admin
from .models import Order, OrderItem, OrderTracker, Address

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'price', 'quantity', 'size', 'color', 'get_total')
    extra = 0
    can_delete = False
    
    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'
    
class OrderTrackerInline(admin.TabularInline):
    model = OrderTracker
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'total_price', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email', 'shipping_address__full_name')
    readonly_fields = ('order_number', 'total_price', 'created_at', 'updated_at')
    inlines = [OrderItemInline, OrderTrackerInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'session_id', 'shipping_address', 'total_price', 'order_note')
        }),
        ('Status', {
            'fields': ('status', 'payment_method')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Create a tracking update when status changes
        if change and 'status' in form.changed_data:
            OrderTracker.objects.create(
                order=obj,
                status=obj.status,
                description=f'Order status updated to {obj.get_status_display()}',
            )
        super().save_model(request, obj, form, change)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'full_address', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('full_name', 'user__username', 'full_address')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'phone', 'email')
        }),
        ('Address', {
            'fields': ('full_address',)
        }),
        ('Settings', {
            'fields': ('is_default', 'created_at')
        }),
    )
