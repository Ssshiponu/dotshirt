from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Product, Category, Image
)

# Register your models here.
# We don't need a specific inline for images as we'll use filter_horizontal


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'alt_text', 'is_feature', 'created_at')
    list_filter = ('is_feature', 'created_at')
    search_fields = ('alt_text',)
    
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return '-'
    thumbnail.short_description = 'Image'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'product_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'sale_price', 'category')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('images',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'category', 'short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        
        ('Media', {
            'fields': ('images',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )