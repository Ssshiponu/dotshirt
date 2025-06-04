from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from order.models import Order, Address
from user.models import User
from django.db.models import Q
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import re

class PhoneRegistrationForm(UserCreationForm):
    username = forms.CharField(
        label="Phone Number",
        max_length=15,
        help_text="Enter a valid phone number (e.g. 01234567890 or +8801234567890)",
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Accepts 11 digits or +880 followed by 10 digits
        if not re.fullmatch(r'(\+8801\d{9}|01\d{9})', username):
            raise forms.ValidationError(
                "Enter a valid phone number (e.g. 01234567890 or +8801234567890)"
            )
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Phone number already exists")
        return username

def register(request):
    """View for user registration"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = PhoneRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PhoneRegistrationForm()

    return render(request, 'user/register.html', {'form': form})
def login_view(request):
    """View for user login"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AuthenticationForm()

    return render(request, 'user/login.html', {'form': form})

def logout_view(request):
    """View for user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def profile(request):
    """View for user profile"""
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        addresses = Address.objects.filter(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        orders = Order.objects.filter(session_id=session_id).order_by('-created_at')
        addresses = []

    context = {
        'orders': orders,
        'addresses': addresses,
    }

    return render(request, 'user/profile.html', context)