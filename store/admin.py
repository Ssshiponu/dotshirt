from django.contrib import admin
from .models import Product, Category, Size, Color, Image, Cart, CartItem

class ProductImageInline(admin.TabularInline):
    model = Product.images.through
    extra = 1
    verbose_name = "Product Image"
    verbose_name_plural = "Product Images"

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['image', 'alt_text']
    search_fields = ['image', 'alt_text']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'sale_price']
    list_filter = ['category']
    search_fields = ['name', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'sale_price']
    inlines = [ProductImageInline]
    exclude = ['images']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        ('Details', {
            'fields': ('description', 'short_description')
        }),
        ('Variants', {
            'fields': ('sizes', 'colors')
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ['product', 'size', 'color', 'quantity']
    raw_id_fields = ['product']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'item_count', 'total_price']
    search_fields = ['user__username', 'session_id']
    inlines = [CartItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    
    def total_price(self, obj):
        return obj.get_total_price()
    
    total_price.short_description = 'Total Price'
    item_count.short_description = 'Items'