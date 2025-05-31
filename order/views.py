from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.urls import reverse

from store.models import Cart, CartItem
from .models import Order, OrderItem, Address, OrderTracker
import uuid

# Create your views here.

def checkout(request):
    """View for displaying the checkout page"""
    # Get cart
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Also check for saved addresses
        addresses = Address.objects.filter(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_id)
        addresses = []
    
    # Check if cart has items
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty. Add some products first.')
        return redirect('store')
    
    context = {
        'cart': cart,
        'addresses': addresses,
    }
    return render(request, 'order/checkout.html', context)

def place_order(request):
    """Handle order placement with cash on delivery"""
    if request.method == 'POST':
        # Get or create cart
        cart = None
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_id = request.session.session_key
            if not session_id:
                request.session.create()
                session_id = request.session.session_key
            cart, created = Cart.objects.get_or_create(session_id=session_id)
        
        # Check if cart has items
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty. Add some products first.')
            return redirect('store')
        
        # Get form data
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        district = request.POST.get('district')
        delivery_charge = request.POST.get('delivery_charge')
        full_address = request.POST.get('full_address')
        order_note = request.POST.get('order_note')
        save_address = request.POST.get('save_address') == 'on'
        
        # Convert delivery charge to decimal
        try:
            delivery_charge = int(delivery_charge)
        except (ValueError, TypeError):
            delivery_charge = 120 if district != 'Dhaka' else 80

        if not district == 'Dhaka' and delivery_charge == 80:
            messages.error(request, 'Delivery charge is not valid for this district.')
            return redirect('checkout')
        
        
        # Create or use existing address
        address_id = request.POST.get('address_id')
        if address_id and address_id != 'new':
            shipping_address = get_object_or_404(Address, id=address_id)
        else:
            # Create new address
            shipping_address = Address(
                full_name=full_name,
                phone=phone,
                email=email,
                full_address=f'{full_address}, {district}',
            )
            
            # Save address to user profile if requested
            if save_address and request.user.is_authenticated:
                shipping_address.user = request.user
                shipping_address.save()
            else:
                shipping_address.save()
        
        # Create order
        order = Order(
            user=request.user if request.user.is_authenticated else None,
            session_id=None if request.user.is_authenticated else request.session.session_key,
            shipping_address=shipping_address,
            delivery_charge=delivery_charge,
            total_price=cart.get_total_price() + delivery_charge,
            payment_method='Cash on Delivery',
        )
        order.save()
        
        # Create order items from cart items
        for cart_item in cart.items.all():
            order_item = OrderItem(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.get_final_price(),
                size=request.POST.get(f'size_{cart_item.id}', ''),
                color=request.POST.get(f'color_{cart_item.id}', ''),
            )
            order_item.save()
        
        # Create initial order tracking
        OrderTracker.objects.create(
            order=order,
            status='pending',
            description='Your order has been placed successfully and is awaiting confirmation.',
        )
        
        # Clear the cart
        cart.items.all().delete()
        
        # Return success
        messages.success(request, f'Your order #{order.order_number} has been placed successfully!')
        return redirect('order_confirmation', order_id=order.id)
    
    # If not POST, redirect to checkout
    return redirect('checkout')

def order_confirmation(request, order_id):
    """Display order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if the user is authorized to view this order
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, 'You are not authorized to view this order.')
            return redirect('profile')
    else:
        if order.user or not order.session_id or order.session_id != request.session.session_key:
            messages.error(request, 'You are not authorized to view this order.')
            return redirect('home')
    
    context = {
        'order': order,
    }
    return render(request, 'order/confirmation.html', context)

@login_required
def order_history(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'order/history.html', context)

@login_required
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'order/detail.html', context)

def order_tracking(request, order_number):
    """Display order tracking page"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Check if the user is authorized to view this order
    if request.user.is_authenticated:
        if order.user and order.user != request.user:
            messages.error(request, 'You are not authorized to view this order.')
            return redirect('profile')
    else:
        if order.user or not order.session_id or order.session_id != request.session.session_key:
            messages.error(request, 'You are not authorized to view this order.')
            return redirect('home')
    
    context = {
        'order': order,
        'tracking_updates': order.tracking_updates.all(),
    }
    return render(request, 'order/tracking.html', context)
