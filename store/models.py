from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

# Create your models here.

class Image(models.Model):
    image = models.ImageField(upload_to='images/')
    alt_text = models.CharField(max_length=255, blank=True, help_text="Alternative text for accessibility")
    is_feature = models.BooleanField(default=False, help_text="Set as the main product image")
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.alt_text if self.alt_text else self.image.url

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ('name',)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Check for duplicate slugs
            if Category.objects.filter(slug=self.slug).exists():
                import uuid
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category', args=[self.id])

class Size(models.Model):
    name = models.CharField(max_length=3)
    
    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, help_text="Hex color code, e.g. #FF0000")
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Stock Keeping Unit")
    price = models.IntegerField()
    sale_price = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    short_description = models.TextField(blank=True, help_text="A brief summary of the product")
    images = models.ManyToManyField(Image, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    sizes = models.ManyToManyField(Size, blank=True)
    colors = models.ManyToManyField(Color, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ('-created_at',)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Check for duplicate slugs
            if Product.objects.filter(slug=self.slug).exists():
                import uuid
                self.slug = f"{self.slug}-{str(uuid.uuid4())[:8]}"

        if not self.sku:
            # Generate a simple SKU based on product name
            import uuid
            name_part = ''.join(word[0] for word in self.name.split()[:3]).upper()
            self.sku = f"{name_part}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        if self.slug:
            return reverse('product_detail_by_slug', args=[self.slug])
        return reverse('product_detail', args=[self.id])
    
    def is_on_sale(self):
        return bool(self.sale_price) and self.sale_price < self.price
    
    def get_discount_percentage(self):
        if self.is_on_sale():
            discount = ((self.price - self.sale_price) / self.price) * 100
            return int(discount)
        return 0
    
    def get_final_price(self):
        if self.is_on_sale():
            return self.sale_price
        return self.price

    def get_primary_image(self):
        if self.images.exists():
            for image in self.images.all():
                if image.is_feature:
                    return image.image.url
        return self.images.first().image.url if self.images.exists() else None

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True, help_text="For anonymous users")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Cart {self.id} - {'User: ' + self.user.email if self.user else 'Anonymous'}"
    
    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_total_price(self):
        return sum(item.get_total() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} {self.size.name if self.size else ''} {self.color.name if self.color else ''}"
    
    def get_total(self):
        return self.product.get_final_price() * self.quantity

    def get_size(self):
        return self.size.name if self.size else ''
    
    def get_color(self):
        return self.color.name if self.color else ''
    
