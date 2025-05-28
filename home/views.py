from django.shortcuts import render
from store.models import Product, Category, Image

# Create your views here.

def home(request):
    # Get featured products
    featured_products = Product.objects.all()[:8]
    
    # Get active categories with products
    categories = Category.objects.all()[:8]
    
    # Get newest products
    newest_products = Product.objects.all().order_by('-created_at')[:8]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'newest_products': newest_products,
    }
    
    return render(request, 'home/home.html', context)
    
def about(request):
    return render(request, 'home/about.html')
    
def contact(request):
    return render(request, 'home/contact.html')
