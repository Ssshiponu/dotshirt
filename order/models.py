from django.db import models
from django.contrib.auth.models import User
from store.models import Product, Cart
from django.utils import timezone

# Create your models here.
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    full_address = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.full_name}, {self.full_address}"
    
    class Meta:
        verbose_name_plural = "Addresses"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)  # For guest checkout
    order_number = models.CharField(max_length=20, unique=True)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    order_note = models.TextField(blank=True, null=True)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Added delivery charge
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, default="Cash on Delivery")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        # Generate a unique order number if not provided
        if not self.order_number:
            # Generate a simple order number based on timestamp and user ID
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M')
            unique_id = str(uuid.uuid4().int)[:4]
            if self.user:
                self.order_number = f"ORD-{timestamp}-{self.user.id}-{unique_id}"
            else:
                self.order_number = f"ORD-{timestamp}-GUEST-{unique_id}"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of purchase
    size = models.CharField(max_length=5, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total(self):
        try:
            return self.price * self.quantity
        except (TypeError, ValueError):
            return self.product.get_final_price() * self.quantity
            
    get_total.short_description = 'Total'

class OrderTracker(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tracking_updates')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"
    
    class Meta:
        ordering = ['-timestamp']
