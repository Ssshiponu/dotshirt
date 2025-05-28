from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.db.models.query_utils import Q

from .models import Profile
from order.models import Order, Address

# Create your views here.
def register(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('profile')
        
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        # Validate form data
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('register')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Update profile
        user.profile.phone = phone
        user.profile.save()
        
        # Log in user
        login(request, user)
        messages.success(request, 'Registration successful! Welcome to Dotshirt.')
        
        # Redirect to profile page
        return redirect('profile')
    
    return render(request, 'user/register.html')

def user_login(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('profile')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Successful login
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect to next page if provided, otherwise to profile
            next_url = request.GET.get('next', 'profile')
            return redirect(next_url)
        else:
            # Invalid login
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'user/login.html')

def user_logout(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def profile(request):
    """Display user profile page"""
    user = request.user
    profile = user.profile
    
    # Get recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get user addresses
    addresses = Address.objects.filter(user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'recent_orders': recent_orders,
        'addresses': addresses,
    }
    
    return render(request, 'user/profile.html', context)

@login_required
def edit_profile(request):
    """Handle profile editing"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        # Get form data
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        profile.phone = request.POST.get('phone')
        
        # Handle date of birth
        dob = request.POST.get('date_of_birth')
        if dob:
            profile.date_of_birth = dob
        
        # Handle profile image
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
        
        # Save changes
        user.save()
        profile.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    context = {
        'user': user,
        'profile': profile,
    }
    
    return render(request, 'user/edit_profile.html', context)

@login_required
def change_password(request):
    """Handle password change"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate passwords
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session after password change
        login(request, request.user)
        
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')
    
    return render(request, 'user/change_password.html')

@login_required
def address_book(request):
    """Display user's address book"""
    addresses = Address.objects.filter(user=request.user)
    
    context = {
        'addresses': addresses,
    }
    
    return render(request, 'user/address_book.html', context)

@login_required
def add_address(request):
    """Handle adding a new address"""
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        is_default = request.POST.get('is_default') == 'on'
        
        # Create address
        address = Address(
            user=request.user,
            full_name=full_name,
            phone=phone,
            email=email,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            postal_code=postal_code,
            is_default=is_default,
        )
        address.save()
        
        # If this is default, unset other defaults
        if is_default:
            Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
        
        messages.success(request, 'Address added successfully.')
        return redirect('address_book')
    
    return render(request, 'user/add_address.html')

@login_required
def edit_address(request, address_id):
    """Handle editing an address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        # Get form data
        address.full_name = request.POST.get('full_name')
        address.phone = request.POST.get('phone')
        address.email = request.POST.get('email')
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.postal_code = request.POST.get('postal_code')
        is_default = request.POST.get('is_default') == 'on'
        address.is_default = is_default
        
        # Save changes
        address.save()
        
        # If this is default, unset other defaults
        if is_default:
            Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
        
        messages.success(request, 'Address updated successfully.')
        return redirect('address_book')
    
    context = {
        'address': address,
    }
    
    return render(request, 'user/edit_address.html', context)

@login_required
def delete_address(request, address_id):
    """Handle deleting an address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    
    messages.success(request, 'Address deleted successfully.')
    return redirect('address_book')
